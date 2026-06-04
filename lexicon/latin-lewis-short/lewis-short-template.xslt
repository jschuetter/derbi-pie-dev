<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html"/>

    <!-- Define constants -->
    <xsl:variable name="bibl_link_pfx">
        https://www.perseus.tufts.edu/hopper/text?doc=
    </xsl:variable>
    <xsl:variable name="lemma_lookup_link_pfx">
        /latin?search=
    </xsl:variable>

    <!-- Convert to <i> tags -->
    <xsl:template match="hi[@rend='ital']">
        <i> <xsl:value-of select="." /> </i>
    </xsl:template>

    <!-- Add link to <bibl> tags if exists -->
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
    
    <!-- Add lemma lookup links to <quote> tags if in Latin? No good way to do this in XSL 1.0 
        Could use Pug instead? -->

    <!-- Mark <quote>, <bibl>, <author> - spans with classes? Links?
        # Parse words in quotes to add links to L&S lemma? -->

    <!-- Ignore these tags -->
    <xsl:template match="sense | case | trans | tr">
        <xsl:apply-templates />
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