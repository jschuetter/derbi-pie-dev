<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html"/>

    <!-- Parameter: sense tag base indentation level -->
    <xsl:param name="base_indent" />
    <xsl:variable name="indent_px" select="50" />

    <!-- RULES: -->
    <!-- <p>, <ref>, <ex> -> <span class="p"> -->
    <!-- <trn>, <com> -> NULL -->
    <!-- <m?> -> <div class="m?"> -->

    <!-- Ignore these tags -->
    <xsl:template match="sense | com | trn">
        <xsl:apply-templates />
    </xsl:template>

    <!-- Leave <i> and <b> tags as-is -->
    <xsl:template match="i | b">
        <xsl:copy>
            <xsl:apply-templates />
        </xsl:copy>
    </xsl:template>

    <!-- Convert <m?> tags to <div>s with indent property -->
    <xsl:template match="m1 | m2 | m3 | m4 | m5">
        <xsl:variable name="indent_lvl" select="number(substring(name(), string-length(name()), 1))" />
        <xsl:variable name="relative_indent" select="$indent_lvl - number($base_indent)" />

        <div>
            <xsl:attribute name="class">oldnorse bodytext</xsl:attribute>
            <xsl:if test="$relative_indent > 0">
                <xsl:attribute name="style">
                    <xsl:value-of select="concat('margin-left=', string($relative_indent * $indent_px), 'px')" />
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates />
        </div>
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