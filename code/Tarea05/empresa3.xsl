<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Empleados a Tiempo Completo</title>
                <link rel="stylesheet" type="text/css" href="empresa3.css"/>
            </head>
            <body>
                <h1>Empleados a Tiempo Completo</h1>
                
                <div class="container">
                    <div class="header-info">
                        <h2>Lista de Empleados con Contrato de Tiempo Completo</h2>
                        <p>Filtrado automático de empleados con <strong>tiempo_completo = true</strong></p>
                    </div>
                    
                    <div class="employees-list">
                        <!-- Iterar sobre todos los empleados -->
                        <xsl:for-each select="empresa/empleados/empleado[tiempo_completo = 'true']">
                            <xsl:sort select="apellido"/>
                            
                            <div class="employee-card">
                                    <div class="employee-header">
                                        <h3 class="employee-name">
                                            <xsl:value-of select="nombre"/>
                                            <xsl:text> </xsl:text>
                                            <xsl:value-of select="apellido"/>
                                        </h3>
                                        <span class="full-time-badge">⏰ Tiempo Completo</span>
                                    </div>
                                    
                                    <div class="employee-details">
                                        <div class="detail-row">
                                            <span class="label">Posición:</span>
                                            <span class="value position">
                                                <xsl:value-of select="posicion"/>
                                            </span>
                                        </div>
                                        
                                        <div class="detail-row">
                                            <span class="label">Salario:</span>
                                            <span class="value salary">
                                                $<xsl:value-of select="format-number(salario, '#,##0')"/>
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
                                            <span class="label">Fecha de Contratación:</span>
                                            <span class="value date">
                                                <xsl:value-of select="fecha_contratacion"/>
                                            </span>
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
