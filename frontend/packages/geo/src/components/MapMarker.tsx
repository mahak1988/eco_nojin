/**
 * Marker — drop a pin on the map at a given coordinate with optional popup.
 */
import { Marker as GLMarker, Popup } from 'react-map-gl/maplibre';
import type { ReactNode } from 'react';

export interface MapMarkerProps {
  latitude: number;
  longitude: number;
  label?: ReactNode;
  color?: string;
  onClick?: () => void;
  popup?: ReactNode;
}

export function MapMarker({
  latitude,
  longitude,
  label,
  color = '#dc2626',
  onClick,
  popup,
}: MapMarkerProps) {
  return (
    <>
      <GLMarker
        latitude={latitude}
        longitude={longitude}
        anchor="bottom"
        onClick={onClick}
      >
        <div
          role="button"
          aria-label={typeof label === 'string' ? label : 'marker'}
          className="cursor-pointer"
          style={{ color }}
        >
          <svg width="24" height="32" viewBox="0 0 24 32" fill="currentColor">
            <path d="M12 0c-6.6 0-12 5.4-12 12 0 8 12 20 12 20s12-12 12-20c0-6.6-5.4-12-12-12zm0 17c-2.8 0-5-2.2-5-5s2.2-5 5-5 5 2.2 5 5-2.2 5-5 5z" />
          </svg>
        </div>
      </GLMarker>
      {popup && (
        <Popup latitude={latitude} longitude={longitude} anchor="top" offset={28}>
          {popup}
        </Popup>
      )}
    </>
  );
}