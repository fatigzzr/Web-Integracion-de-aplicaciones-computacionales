<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Empleados por Fecha de Contratación</title>
                <link rel="stylesheet" type="text/css" href="empresa4.css"/>
            </head>
            <body>
                <h1>Empleados por Fecha de Contratación</h1>
                
                <div class="container">
                    <div class="header-info">
                        <h2>Informe de Empleados Ordenados por Antigüedad</h2>
                        <p>Lista ordenada de <strong>más antiguos a más nuevos</strong> según fecha de contratación</p>
                    </div>
                    
                    <div class="employees-timeline">
                        <!-- Iterar sobre todos los empleados ordenados por fecha de contratación -->
                        <xsl:for-each select="empresa/empleados/empleado">
                            <xsl:sort select="fecha_contratacion" order="ascending"/>
                            
                            <div class="employee-item">
                                <div class="timeline-marker">
                                    <div class="date-badge">
                                        <xsl:value-of select="substring(fecha_contratacion, 1, 4)"/>
                                    </div>
                                </div>
                                
                                <div class="employee-content">
                                    <div class="employee-header">
                                        <h3 class="employee-name">
                                            <xsl:value-of select="nombre"/>
                                            <xsl:text> </xsl:text>
                                            <xsl:value-of select="apellido"/>
                                        </h3>
                                        <span class="hire-date">
                                            📅 <xsl:value-of select="fecha_contratacion"/>
                                        </span>
                                    </div>
                                    
                                    <div class="employee-details">
                                        <div class="detail-row">
                                            <span class="label">Posición:</span>
                                            <span class="value position">
                                                <xsl:value-of select="posicion"/>
                                            </span>
                                        </div>
                                        
                                        <div class="detail-row">
                                            <span class="label">Departamento:</span>
                                            <span class="value department">
                                                <xsl:variable name="dept-id" select="id_departamento"/>
                                                <xsl:value-of select="../../departamentos/departamento[@id = $dept-id]/nombre"/>
                                            </span>
                                        </div>
                                        
                                        <div class="detail-row">
                                            <span class="label">Salario:</span>
                                            <span class="value salary">
                                                $<xsl:value-of select="format-number(salario, '#,##0')"/>
                                            </span>
                                        </div>
                                        
                                        <div class="detail-row">
                                            <span class="label">Tipo de Contrato:</span>
                                            <span class="value contract-type">
                                                <xsl:choose>
                                                    <xsl:when test="tiempo_completo = 'true'">
                                                        <span class="full-time">⏰ Tiempo Completo</span>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <span class="part-time">⏱️ Tiempo Parcial</span>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </xsl:for-each>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
