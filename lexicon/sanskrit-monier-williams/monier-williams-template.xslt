<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="html"/>

    <!-- RULES: -->
    <!-- <s>, <s1> -> <span class="s">, *transliterate contents to IAST* -->
    <!-- N.B. <srs/> => CIRCUMFLEX ACCENT -->
    <!-- <lex>, <ls> -> <span class="lex"> -->
    <!-- <info>, <listinfo> -> drop tag -->

    <!-- Drop these tags -->
    <xsl:template match="info | listinfo | pb" />

    <!-- Ignore these tags -->
    <!-- Replace <body> with <div> after stripping spaces in Python -->
    <xsl:template match="body">
        <xsl:apply-templates />
    </xsl:template>

    <!-- Leave <i> and <b> tags as-is -->
    <xsl:template match="i | b | s">
        <xsl:copy>
            <xsl:apply-templates />
        </xsl:copy>
    </xsl:template>

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

    <!-- Generic rule to convert tags to spans with name as class -->
    <xsl:template match="text()">
        <xsl:value-of select="."/>
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