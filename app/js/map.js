// need to do something about this
mapboxgl.accessToken =
  "pk.eyJ1IjoiZ2VvcmdlazcyMiIsImEiOiJjbDlhaG05aG0waGJjM3hxd29sNmV1bnUwIn0.5BQvW7-_lTlIbS36AjRs7g";

var createGeoJSONCircle = function (center, radiusInKm, points) {
  if (!points) points = 64;

  var coords = {
    latitude: center[1],
    longitude: center[0],
  };

  var km = radiusInKm;

  var ret = [];
  var distanceX = km / (111.32 * Math.cos((coords.latitude * Math.PI) / 180));
  var distanceY = km / 110.574;

  var theta, x, y;
  for (var i = 0; i < points; i++) {
    theta = (i / points) * (2 * Math.PI);
    x = distanceX * Math.cos(theta);
    y = distanceY * Math.sin(theta);

    ret.push([coords.longitude + x, coords.latitude + y]);
  }
  ret.push(ret[0]);

  return {
    type: "geojson",
    data: {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: {
            type: "Polygon",
            coordinates: [ret],
          },
        },
      ],
    },
  };
};

function getLocation(callback) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(callback);
  } else {
    x.innerHTML = "Geolocation is not supported by this browser.";
  }
}

function getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2) {
  var R = 6371; // Radius of the earth in km
  var dLat = deg2rad(lat2 - lat1); // deg2rad below
  var dLon = deg2rad(lon2 - lon1);
  var a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(deg2rad(lat1)) *
      Math.cos(deg2rad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  var d = R * c; // Distance in km
  return d * 1000;
}

function deg2rad(deg) {
  return deg * (Math.PI / 180);
}

class Map {
  constructor(containerName, long, lat, radius, followUser, checkinCallback) {
    this.map = new mapboxgl.Map({
      container: containerName, // container id
      // Choose from Mapbox's core styles, or make your own style with Mapbox Studio
      style: "mapbox://styles/mapbox/streets-v11",
      center: [long, lat], // starting position
      zoom: 17, // starting zoom
      interactive: !followUser,
    });

    if (!followUser) {
      this.map.addControl(new mapboxgl.NavigationControl());
    }
    // Create a marker and add it to the map.
    this.marker = new mapboxgl.Marker()
      .setLngLat([long, lat])
      .setDraggable(!followUser)
      .addTo(this.map);
    this.radius = radius;
    this.checkinCallback = checkinCallback;
    this.marker.on("dragend", () => {
      if (this.map.isSourceLoaded("polygon")) {
        this.drawCircle(this.radius);
      }
    });

    this.map.on("load", () => {
      this.map.addSource("polygon", createGeoJSONCircle([0, 0], 0));
      this.map.addLayer({
        id: "polygon",
        type: "fill",
        source: "polygon",
        layout: {},
        paint: {
          "fill-color": "blue",
          "fill-opacity": 0.6,
        },
      });

      this.drawCircle(this.radius);

      if (followUser) {
        this.userMarker = new mapboxgl.Marker({ color: "red" })
          .setLngLat([0, 0])
          .addTo(this.map);
        this.followUser();
      }
    });
  }

  updateMap(long, lat) {
    this.map.setCenter([long, lat]);
    this.marker.setLngLat([long, lat]);
  }

  getPointerCoordinates() {
    const lngLat = this.marker.getLngLat();
    return [lngLat["lng"], lngLat["lat"]];
  }

  followUser() {
    getLocation((pos) => {
      let userLngLat = [pos.coords.longitude, pos.coords.latitude];
      let venueLngLat = this.getPointerCoordinates();
      this.map.fitBounds([userLngLat, this.getPointerCoordinates()], {
        padding: { top: 50, right: 50, bottom: 50, left: 50 },
      });
      this.userMarker.setLngLat(userLngLat);

      console.log(
        getDistanceFromLatLonInKm(
          userLngLat[1],
          userLngLat[0],
          venueLngLat[1],
          venueLngLat[0]
        ) < this.radius
      );
      if (
        getDistanceFromLatLonInKm(
          userLngLat[1],
          userLngLat[0],
          venueLngLat[1],
          venueLngLat[0]
        ) < this.radius
      ) {
        this.checkinCallback();
      } else {
        setTimeout(() => {
          this.followUser();
        }, 2000);
      }
    });
  }

  drawCircle(radius) {
    this.radius = radius;
    const lngLat = this.getPointerCoordinates();
    this.map
      .getSource("polygon")
      .setData(createGeoJSONCircle(lngLat, radius / 1000).data);
  }
}
