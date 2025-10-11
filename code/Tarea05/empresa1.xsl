<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Empleados por Departamento</title>
                <link rel="stylesheet" type="text/css" href="empresa1.css"/>
            </head>
            <body>
                <h1>Empleados por Departamento</h1>
                
                <!-- Iterar sobre cada departamento -->
                <xsl:for-each select="empresa/departamentos/departamento">
                    <xsl:sort select="nombre"/>
                    
                    <xsl:variable name="dept-id" select="@id"/>
                    
                    <!-- Verificar si hay empleados en este departamento -->
                    <xsl:if test="../..//empleado[id_departamento = $dept-id]">
                        <div class="department-section">
                            <!-- Encabezado del departamento -->
                            <div class="department-header">
                                <xsl:value-of select="nombre"/>
                            </div>
                            <div class="department-location">
                                📍 <xsl:value-of select="localizacion"/>
                            </div>
                            
                            <!-- Tabla de empleados -->
                            <table>
                                <thead>
                                    <tr>
                                        <th>Nombre Completo</th>
                                        <th>Posición</th>
                                        <th>Salario</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- Mostrar empleados de este departamento -->
                                    <xsl:for-each select="../../empleados/empleado[id_departamento = $dept-id]">
                                        <xsl:sort select="apellido"/>
                                        <tr>
                                            <td class="employee-name">
                                                <xsl:value-of select="nombre"/>
                                                <xsl:text> </xsl:text>
                                                <xsl:value-of select="apellido"/>
                                            </td>
                                            <td>
                                                <xsl:value-of select="posicion"/>
                                            </td>
                                            <td class="salary">
                                                $<xsl:value-of select="format-number(salario, '#,##0')"/>
                                            </td>
                                        </tr>
                                    </xsl:for-each>
                                </tbody>
                            </table>
                        </div>
                    </xsl:if>
                </xsl:for-each>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
