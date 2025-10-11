<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Estructura Jerárquica de la Empresa</title>
                <link rel="stylesheet" type="text/css" href="empresa5.css"/>
            </head>
            <body>
                <h1>Estructura Jerárquica de la Empresa</h1>
                
                <div class="container">
                    <div class="header-info">
                        <h2>Organización por Departamentos</h2>
                        <p>Vista jerárquica de la estructura organizacional con empleados agrupados por departamento</p>
                    </div>
                    
                    <div class="hierarchy-container">
                        <!-- Iterar sobre cada departamento -->
                        <xsl:for-each select="empresa/departamentos/departamento">
                            <xsl:sort select="nombre"/>
                            
                            <xsl:variable name="dept-id" select="@id"/>
                            <xsl:variable name="dept-employees" select="../../empleados/empleado[id_departamento = $dept-id]"/>
                            
                            <!-- Solo mostrar departamentos que tienen empleados -->
                            <xsl:if test="$dept-employees">
                                <div class="department-section">
                                    <!-- Encabezado del departamento -->
                                    <div class="department-header">
                                        <div class="department-info">
                                            <h3 class="department-name">
                                                <xsl:value-of select="nombre"/>
                                            </h3>
                                            <p class="department-location">
                                                📍 <xsl:value-of select="localizacion"/>
                                            </p>
                                        </div>
                                        <div class="department-stats">
                                            <span class="employee-count">
                                                👥 <xsl:value-of select="count($dept-employees)"/> empleado<xsl:if test="count($dept-employees) != 1">s</xsl:if>
                                            </span>
                                        </div>
                                    </div>
                                    
                                    <!-- Lista de empleados del departamento -->
                                    <div class="employees-list">
                                        <xsl:for-each select="$dept-employees">
                                            <xsl:sort select="apellido"/>
                                            
                                            <div class="employee-item">
                                                <div class="employee-main-info">
                                                    <h4 class="employee-name">
                                                        <xsl:value-of select="nombre"/>
                                                        <xsl:text> </xsl:text>
                                                        <xsl:value-of select="apellido"/>
                                                    </h4>
                                                    <span class="employee-position">
                                                        <xsl:value-of select="posicion"/>
                                                    </span>
                                                </div>
                                                
                                                <div class="employee-details">
                                                    <div class="contract-type">
                                                        <xsl:choose>
                                                            <xsl:when test="tiempo_completo = 'true'">
                                                                <span class="full-time-badge">⏰ Tiempo Completo</span>
                                                            </xsl:when>
                                                            <xsl:otherwise>
                                                                <span class="part-time-badge">⏱️ Tiempo Parcial</span>
                                                            </xsl:otherwise>
                                                        </xsl:choose>
                                                    </div>
                                                    
                                                    <div class="additional-info">
                                                        <span class="salary-info">
                                                            💰 $<xsl:value-of select="format-number(salario, '#,##0')"/>
                                                        </span>
                                                        <span class="hire-date-info">
                                                            📅 <xsl:value-of select="fecha_contratacion"/>
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </xsl:for-each>
                                    </div>
                                </div>
                            </xsl:if>
                        </xsl:for-each>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
