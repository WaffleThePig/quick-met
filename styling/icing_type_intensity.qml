<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.44.8-Solothurn" styleCategories="Symbology">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option value="" type="QString" name="name"/>
      <Option name="properties"/>
      <Option value="collection" type="QString" name="type"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour" enabled="false" maxOversampling="2"/>
    </provider>
    <rasterrenderer nodataColor="" alphaBand="-1" opacity="1" band="1" type="paletted">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry value="0" alpha="0" label="No Significant Icing" color="#ffffff"/>
        <paletteEntry value="1" alpha="255" label="Trace Rime" color="#fcfdbf"/>
        <paletteEntry value="2" alpha="255" label="Light Rime" color="#9c5e00"/>
        <paletteEntry value="3" alpha="255" label="Light Mixed" color="#6ba400"/>
        <paletteEntry value="5" alpha="255" label="Moderate Rime" color="#4d2e00"/>
        <paletteEntry value="6" alpha="255" label="Moderate Mixed" color="#00bc9b"/>
      </colorPalette>
      <colorramp type="randomcolors" name="[source]">
        <Option/>
      </colorramp>
    </rasterrenderer>
    <brightnesscontrast gamma="1" brightness="0" contrast="0"/>
    <huesaturation saturation="0" invertColors="0" colorizeStrength="100" colorizeOn="0" colorizeBlue="128" colorizeRed="255" grayscaleMode="0" colorizeGreen="128"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
