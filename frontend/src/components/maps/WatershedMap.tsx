// frontend/src/components/maps/WatershedMap.tsx
import Map, { Layer, Source } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

export function WatershedMap({ watershedGeoJson }: Props) {
  return (
    <Map
      initialViewState={{
        longitude: 51.5,
        latitude: 35.5,
        zoom: 12 }}
      style={{ width: '100%', height: '600px' }}
      mapStyle="https://demotiles.maplibre.org/style.json"
    >
      <Source id="watershed" type="geojson" data={watershedGeoJson}>
        <Layer
          id="watershed-fill"
          type="fill"
          paint={{
            'fill-color': '#088',
            'fill-opacity': 0.3 }}
        />
      </Source>
    </Map>
  );
}