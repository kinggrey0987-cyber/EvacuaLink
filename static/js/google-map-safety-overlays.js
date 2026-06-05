(function(window) {
    const riskStyles = {
        CRITICAL: { color: "#dc3545", radius: 820, heatWeight: 1.0, scale: 11 },
        HIGH: { color: "#ff8c00", radius: 700, heatWeight: 0.82, scale: 9 },
        MODERATE: { color: "#ffc107", radius: 560, heatWeight: 0.58, scale: 8 },
        LOW: { color: "#22c55e", radius: 420, heatWeight: 0.35, scale: 7 }
    };

    function escapeHtml(value) {
        return String(value || "").replace(/[&<>"']/g, function(character) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"
            }[character];
        });
    }

    function positionFrom(item) {
        return {
            lat: Number(item.latitude),
            lng: Number(item.longitude)
        };
    }

    function popupHtml(title, label, details) {
        return "<div style=\"font-size: 14px; min-width: 190px;\">" +
            "<strong>" + escapeHtml(title) + "</strong><br>" +
            "<small>" + label + "</small>" +
            (details ? "<div class=\"mt-2\">" + details + "</div>" : "") +
            "</div>";
    }

    function addHeatArea(points, position, radiusMeters, weight) {
        const latMeters = 111320;
        const lngMeters = 111320 * Math.cos(position.lat * Math.PI / 180);
        const rings = [
            { distance: 0, weight: weight },
            { distance: radiusMeters * 0.22, weight: weight * 0.86 },
            { distance: radiusMeters * 0.46, weight: weight * 0.58 },
            { distance: radiusMeters * 0.68, weight: weight * 0.32 }
        ];
        const bearings = [0, 45, 90, 135, 180, 225, 270, 315];

        rings.forEach(function(ring) {
            if (ring.distance === 0) {
                points.push({
                    location: new google.maps.LatLng(position.lat, position.lng),
                    weight: ring.weight
                });
                return;
            }

            bearings.forEach(function(degrees) {
                const radians = degrees * Math.PI / 180;
                points.push({
                    location: new google.maps.LatLng(
                        position.lat + (Math.cos(radians) * ring.distance / latMeters),
                        position.lng + (Math.sin(radians) * ring.distance / lngMeters)
                    ),
                    weight: ring.weight
                });
            });
        });
    }

    function boundaryPathFromGeoJson(geometry) {
        if (!geometry || geometry.type !== "Polygon" || !geometry.coordinates || !geometry.coordinates[0]) {
            return [];
        }

        return geometry.coordinates[0].map(function(coordinate) {
            return { lat: Number(coordinate[1]), lng: Number(coordinate[0]) };
        });
    }

    function addOutsideBoundaryMask(map, geometry) {
        const boundaryPath = boundaryPathFromGeoJson(geometry);

        if (!boundaryPath.length) {
            return;
        }

        const overlay = new google.maps.OverlayView();

        overlay.onAdd = function() {
            const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            svg.style.height = "1px";
            svg.style.left = "0";
            svg.style.overflow = "visible";
            svg.style.pointerEvents = "none";
            svg.style.position = "absolute";
            svg.style.top = "0";
            svg.style.width = "1px";
            path.setAttribute("fill", "rgba(15, 35, 65, 0.16)");
            path.setAttribute("fill-rule", "evenodd");
            path.setAttribute("stroke", "none");
            svg.appendChild(path);
            this.svg = svg;
            this.path = path;
            this.getPanes().overlayLayer.appendChild(svg);
        };

        overlay.draw = function() {
            const projection = this.getProjection();
            const bounds = map.getBounds();

            if (!projection || !bounds || !this.path) {
                return;
            }

            const northEast = projection.fromLatLngToDivPixel(bounds.getNorthEast());
            const southWest = projection.fromLatLngToDivPixel(bounds.getSouthWest());
            const viewport = [
                "M " + southWest.x + " " + northEast.y,
                "L " + northEast.x + " " + northEast.y,
                "L " + northEast.x + " " + southWest.y,
                "L " + southWest.x + " " + southWest.y,
                "Z"
            ].join(" ");
            const boundary = boundaryPath.map(function(point, index) {
                const pixel = projection.fromLatLngToDivPixel(new google.maps.LatLng(point.lat, point.lng));
                return (index === 0 ? "M" : "L") + " " + pixel.x + " " + pixel.y;
            }).join(" ") + " Z";

            this.path.setAttribute("d", viewport + " " + boundary);
        };

        overlay.onRemove = function() {
            if (this.svg) {
                this.svg.remove();
                this.svg = null;
                this.path = null;
            }
        };

        overlay.setMap(map);
    }

    function markerIcon(color, scale) {
        return {
            path: google.maps.SymbolPath.CIRCLE,
            fillColor: color,
            fillOpacity: 0.95,
            strokeColor: "#ffffff",
            strokeWeight: 3,
            scale: scale
        };
    }

    function addSafetyOverlays(map, payload, options) {
        const infoWindow = new google.maps.InfoWindow();
        const overlays = {
            bounds: new google.maps.LatLngBounds(),
            markerCount: 0
        };
        const settings = Object.assign({
            showBoundaryMask: true,
            showHeatmap: true,
            showHazardMarkers: true,
            showSafeZones: true,
            showEvacuationCenters: true,
            hazardFillOpacity: 0.18,
            hazardStrokeOpacity: 0.18,
            heatmapOpacity: 0.88,
            heatmapRadius: 72
        }, options || {});

        if (payload.boundary) {
            map.data.addGeoJson({
                type: "Feature",
                properties: { name: "Barangay Alicante" },
                geometry: payload.boundary
            });
            map.data.setStyle({
                strokeColor: "#0066cc",
                strokeOpacity: 0.9,
                strokeWeight: 3,
                fillColor: "#0066cc",
                fillOpacity: 0.04
            });

            if (settings.showBoundaryMask) {
                addOutsideBoundaryMask(map, payload.boundary);
            }
        }

        if (settings.showHeatmap) {
            const heatPoints = [];
            (payload.hazardZones || []).forEach(function(zone) {
                const style = riskStyles[zone.risk_level] || riskStyles.LOW;
                const position = positionFrom(zone);
                addHeatArea(heatPoints, position, style.radius, style.heatWeight);
                new google.maps.Circle({
                    map: map,
                    center: position,
                    radius: style.radius,
                    strokeColor: style.color,
                    strokeOpacity: settings.hazardStrokeOpacity,
                    strokeWeight: 1,
                    fillColor: style.color,
                    fillOpacity: settings.hazardFillOpacity
                });
            });

            if (heatPoints.length > 0) {
                new google.maps.visualization.HeatmapLayer({
                    map: map,
                    data: heatPoints,
                    radius: settings.heatmapRadius,
                    opacity: settings.heatmapOpacity,
                    dissipating: true,
                    gradient: [
                        "rgba(0, 255, 0, 0)",
                        "rgba(70, 255, 0, 0.48)",
                        "rgba(190, 255, 0, 0.64)",
                        "rgba(255, 230, 0, 0.78)",
                        "rgba(255, 128, 0, 0.88)",
                        "rgba(255, 0, 0, 0.96)"
                    ]
                });
            }
        }

        if (settings.showHazardMarkers) {
            (payload.hazardZones || []).forEach(function(zone) {
                const style = riskStyles[zone.risk_level] || riskStyles.LOW;
                const position = positionFrom(zone);
                const marker = new google.maps.Marker({
                    map: map,
                    position: position,
                    title: zone.name,
                    icon: markerIcon(style.color, style.scale)
                });
                marker.addListener("click", function() {
                    infoWindow.setContent(popupHtml(
                        zone.name,
                        "Hazard Zone",
                        "<strong>Type:</strong> " + escapeHtml(zone.hazard_type) + "<br>" +
                        "<strong>Risk Level:</strong> " + escapeHtml(zone.risk_level) +
                        (zone.description ? "<p class=\"mb-0 mt-2\">" + escapeHtml(zone.description) + "</p>" : "")
                    ));
                    infoWindow.open(map, marker);
                });
                overlays.bounds.extend(position);
                overlays.markerCount += 1;
            });
        }

        if (settings.showSafeZones) {
            (payload.safeZones || []).forEach(function(zone) {
                const position = positionFrom(zone);
                new google.maps.Circle({
                    map: map,
                    center: position,
                    radius: 260,
                    strokeColor: "#28a745",
                    strokeOpacity: 0.72,
                    strokeWeight: 2,
                    fillColor: "#28a745",
                    fillOpacity: 0.16
                });
                const marker = new google.maps.Marker({
                    map: map,
                    position: position,
                    title: zone.name,
                    icon: markerIcon("#28a745", 8)
                });
                marker.addListener("click", function() {
                    infoWindow.setContent(popupHtml(
                        zone.name,
                        "Safe Zone",
                        zone.description ? "<p class=\"mb-0\">" + escapeHtml(zone.description) + "</p>" : ""
                    ));
                    infoWindow.open(map, marker);
                });
                overlays.bounds.extend(position);
                overlays.markerCount += 1;
            });
        }

        if (settings.showEvacuationCenters) {
            (payload.evacuationCenters || []).forEach(function(centerItem) {
                const position = positionFrom(centerItem);
                const marker = new google.maps.Marker({
                    map: map,
                    position: position,
                    title: centerItem.name,
                    icon: markerIcon("#0d6efd", 12),
                    zIndex: 1000
                });
                marker.addListener("click", function() {
                    infoWindow.setContent(popupHtml(
                        centerItem.name,
                        "Evacuation Center",
                        centerItem.address || centerItem.description
                            ? "<p class=\"mb-0\">" + escapeHtml(centerItem.address || centerItem.description) + "</p>"
                            : ""
                    ));
                    infoWindow.open(map, marker);
                });
                overlays.bounds.extend(position);
                overlays.markerCount += 1;
            });
        }

        return overlays;
    }

    window.EvacuaLinkMaps = {
        addSafetyOverlays: addSafetyOverlays,
        addOutsideBoundaryMask: addOutsideBoundaryMask,
        markerIcon: markerIcon,
        positionFrom: positionFrom,
        riskStyles: riskStyles
    };
})(window);
