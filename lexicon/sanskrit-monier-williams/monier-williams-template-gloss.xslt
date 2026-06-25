<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="html"/>

    <!-- Same as primary MW XSLT template, but drops <ls>, <lex>
         and does not wrap remaining tags in <span> -->

    <!-- Drop these tags -->
    <xsl:template match="info | listinfo | pb | ls | lex" />

    <!-- Replace <srs/> with combining circumflex -->
    <xsl:template match="srs">
        <xsl:text>&#x0302;</xsl:text>
    </xsl:template>

    <!-- Check for abbreviation attribute in <s1> tags -->
    <xsl:template match="s1">
        <span>
            <xsl:attribute name="class">s1</xsl:attribute>
            <xsl:choose>
                <xsl:when test="@n">
                    <xsl:value-of select="@n" />
                </xsl:when>
                <xsl:when test="not(@foo)">
                    <xsl:apply-templates />
                </xsl:when>
            </xsl:choose>
        </span>
    </xsl:template>

    <!-- Ignore all other tags -->
    <xsl:template match="text()">
        <xsl:value-of select="."/>
    </xsl:template>

    <xsl:template match="*">
        <xsl:apply-templates />
    </xsl:template>

</xsl:stylesheet>