<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html"/>

    <!-- Add URN to <bibl> tags if exists -->
    <xsl:template match="bibl">
        <span>
            <xsl:attribute name="class">
                <xsl:value-of select="name()"/>
            </xsl:attribute>
            <xsl:if test="@n">
                <xsl:attribute name="urn">
                    <xsl:value-of select="@n"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates />
        </span>
    </xsl:template>
    <!-- Add grammar type to <gram> tags if exists -->
    <xsl:template match="gram">
        <span>
            <xsl:attribute name="class">
                <xsl:value-of select="name()"/>
                <xsl:if test="@n">
                    <xsl:value-of select=" @n"/>
                </xsl:if>
            </xsl:attribute>
            <xsl:apply-templates />
        </span>
    </xsl:template>
    
    <!-- Ignore these tags -->
    <xsl:template match="entry | sense | case | trans | gramGrp | xr | lbl">
        <xsl:apply-templates />
    </xsl:template>

    <!-- Insert space around <tr> and <foreign> -->
    <xsl:template match="tr">
        <xsl:text> </xsl:text>
        <xsl:apply-templates />
        <xsl:text> </xsl:text>
    </xsl:template>
    <!-- Include <span> for <foreign> tags -->
    <xsl:template match="foreign">
        <xsl:text> </xsl:text>
        <span>
            <xsl:attribute name="class">
                <xsl:value-of select="name()" />
            </xsl:attribute>
            <xsl:apply-templates />
        </span>
        <xsl:text> </xsl:text>
    </xsl:template>

    <!-- Generic rule to convert tags to spans with name as class -->
    <xsl:template match="text()">
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:template>

    <xsl:template match="*">
        <span>
            <xsl:attribute name="class">
                <xsl:value-of select="name()"/>
            </xsl:attribute>
            <xsl:apply-templates />
        </span>
    </xsl:template>


</xsl:stylesheet>