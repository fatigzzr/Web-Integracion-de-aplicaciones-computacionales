<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Salarios Promedio por Departamento</title>
                <link rel="stylesheet" type="text/css" href="empresa2.css"/>
            </head>
            <body>
                <h1>Salarios Promedio por Departamento</h1>
                
                <div class="summary-container">
                    <div class="summary-header">
                        <h2>Resumen de Salarios por Departamento</h2>
                        <p>Análisis estadístico de los salarios promedio en cada departamento</p>
                    </div>
                    
                    <div class="departments-list">
                        <!-- Iterar sobre cada departamento -->
                        <xsl:for-each select="empresa/departamentos/departamento">
                            <xsl:sort select="nombre"/>
                            
                            <xsl:variable name="dept-id" select="@id"/>
                            <xsl:variable name="dept-employees" select="../../empleados/empleado[id_departamento = $dept-id]"/>
                            
                            <!-- Solo mostrar departamentos que tienen empleados -->
                            <xsl:if test="$dept-employees">
                                <xsl:variable name="total-salaries">
                                    <xsl:call-template name="sum-salaries">
                                        <xsl:with-param name="employees" select="$dept-employees"/>
                                    </xsl:call-template>
                                </xsl:variable>
                                
                                <xsl:variable name="employee-count" select="count($dept-employees)"/>
                                <xsl:variable name="average-salary" select="$total-salaries div $employee-count"/>
                                
                                <xsl:variable name="min-salary">
                                    <xsl:call-template name="min-salary">
                                        <xsl:with-param name="employees" select="$dept-employees"/>
                                    </xsl:call-template>
                                </xsl:variable>
                                
                                <xsl:variable name="max-salary">
                                    <xsl:call-template name="max-salary">
                                        <xsl:with-param name="employees" select="$dept-employees"/>
                                    </xsl:call-template>
                                </xsl:variable>
                                
                                <div class="department-item">
                                    <div class="department-info">
                                        <h3 class="department-name">
                                            <xsl:value-of select="nombre"/>
                                        </h3>
                                        <p class="department-location">
                                            📍 <xsl:value-of select="localizacion"/>
                                        </p>
                                        <p class="employee-count">
                                            👥 <xsl:value-of select="$employee-count"/> empleado<xsl:if test="$employee-count != 1">s</xsl:if>
                                        </p>
                                    </div>
                                    
                                    <div class="salary-info">
                                        <div class="average-salary">
                                            <span class="salary-label">Salario Promedio:</span>
                                            <span class="salary-value">
                                                $<xsl:value-of select="format-number($average-salary, '#,##0.00')"/>
                                            </span>
                                        </div>
                                        
                                        <div class="salary-range">
                                            <span class="min-salary">
                                                Mín: $<xsl:value-of select="format-number($min-salary, '#,##0')"/>
                                            </span>
                                            <span class="max-salary">
                                                Máx: $<xsl:value-of select="format-number($max-salary, '#,##0')"/>
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </xsl:if>
                        </xsl:for-each>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
    
    <!-- Template recursivo para sumar salarios -->
    <xsl:template name="sum-salaries">
        <xsl:param name="employees"/>
        <xsl:param name="sum" select="0"/>
        
        <xsl:choose>
            <xsl:when test="$employees">
                <xsl:call-template name="sum-salaries">
                    <xsl:with-param name="employees" select="$employees[position() > 1]"/>
                    <xsl:with-param name="sum" select="$sum + $employees[1]/salario"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sum"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- Template para encontrar el salario mínimo -->
    <xsl:template name="min-salary">
        <xsl:param name="employees"/>
        <xsl:param name="min" select="999999999"/>
        
        <xsl:choose>
            <xsl:when test="$employees">
                <xsl:variable name="current-salary" select="$employees[1]/salario"/>
                <xsl:variable name="new-min">
                    <xsl:choose>
                        <xsl:when test="$current-salary &lt; $min">
                            <xsl:value-of select="$current-salary"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$min"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:call-template name="min-salary">
                    <xsl:with-param name="employees" select="$employees[position() > 1]"/>
                    <xsl:with-param name="min" select="$new-min"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$min"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- Template para encontrar el salario máximo -->
    <xsl:template name="max-salary">
        <xsl:param name="employees"/>
        <xsl:param name="max" select="0"/>
        
        <xsl:choose>
            <xsl:when test="$employees">
                <xsl:variable name="current-salary" select="$employees[1]/salario"/>
                <xsl:variable name="new-max">
                    <xsl:choose>
                        <xsl:when test="$current-salary > $max">
                            <xsl:value-of select="$current-salary"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$max"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:call-template name="max-salary">
                    <xsl:with-param name="employees" select="$employees[position() > 1]"/>
                    <xsl:with-param name="max" select="$new-max"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$max"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
