# 🔥 Fire Danger Index (FDI) for Home Assistant

A Home Assistant automation package that calculates the Fire Danger Index (FDI) using the **McArthur Forest Fire Danger Index (FFDI) Mark 5** formula, as used by the CFA (Country Fire Authority) in Australia.

## 📋 Features

- **Real-time FDI Calculation**: Uses temperature, wind speed, humidity, and drought factor
- **15-minute Updates**: Automatically recalculates every 15 minutes between 1:00 AM and 11:45 PM
- **Interactive Graph**: ApexCharts-powered graph with danger level annotations
- **3-Day History**: View today, yesterday, or 2 days ago with easy day navigation
- **Configurable Alerts**: Set your own threshold with notification support (disabled by default)
- **Drought Factor Control**: Adjustable drought factor (1-10) based on local conditions
- **Color-coded Danger Levels**: Visual indicators for each danger rating

## 📊 FDI Danger Ratings

| Rating | FDI Range | Color |
|--------|-----------|-------|
| Low-Moderate | 0-11 | 🟢 Green |
| High | 12-24 | 🟡 Yellow |
| Very High | 25-49 | 🟠 Orange |
| Severe | 50-74 | 🔴 Red |
| Extreme | 75-99 | 🟣 Purple |
| Catastrophic | 100+ | ⚫ Black |

## 🧮 The Formula

The McArthur FFDI Mark 5 formula used:

```
FFDI = 2 × exp(-0.45 + 0.987×ln(DF) + 0.0338×T + 0.0234×U - 0.0345×H)
```

Where:
- **T** = Temperature (°C)
- **U** = Wind speed (km/h)
- **H** = Relative humidity (%)
- **DF** = Drought Factor (1-10, user configurable)

## 📦 Requirements

1. **Home Assistant** (2023.x or later recommended)
2. **Ecowitt Weather Station** configured in Home Assistant
3. **ApexCharts Card** - Install via HACS:
   - Open HACS → Frontend → Search "ApexCharts Card" → Install

## 🚀 Installation

### Step 1: Copy the Configuration File

Copy `fire_danger_index.yaml` to your Home Assistant config directory:

```bash
# Via SSH or File Editor
cp fire_danger_index.yaml /config/packages/
```

Or use the File Editor add-on to create the file.

### Step 2: Enable Packages in configuration.yaml

Add the following to your `configuration.yaml`:

```yaml
homeassistant:
  packages:
    fire_danger: !include packages/fire_danger_index.yaml
```

If you already have a packages section, just add the fire_danger line.

### Step 3: Update Sensor Entity IDs

**IMPORTANT**: Edit `fire_danger_index.yaml` and replace the sensor entity IDs with your actual Ecowitt sensor names.

Find these lines in the template sensor:

```yaml
{% set temp = states('sensor.ecowitt_temperature') | float(0) %}
{% set wind = states('sensor.ecowitt_wind_speed') | float(0) %}
{% set humidity = states('sensor.ecowitt_humidity') | float(50) %}
```

Replace with your actual sensor entity IDs. Common Ecowitt patterns:
- `sensor.gw1000_temperature`
- `sensor.gw1000_wind_speed_km_h`
- `sensor.gw1000_humidity`

To find your sensor names:
1. Go to Developer Tools → States
2. Search for "temperature", "wind", or "humidity"
3. Look for sensors from your Ecowitt device

### Step 4: Restart Home Assistant

Go to Developer Tools → YAML → Check Configuration → Restart

### Step 5: Add the Dashboard Card

1. Edit your dashboard
2. Click "+ Add Card" → "Manual"
3. Copy and paste the contents of `dashboard_card.yaml`
4. Update the weather condition sensor entity IDs at the bottom
5. Save

## ⚙️ Configuration Options

### Drought Factor

The drought factor (1-10) represents how dry the vegetation is:
- **1-3**: Recent significant rainfall
- **4-6**: Normal/moderate conditions
- **7-10**: Extended dry period, very dry vegetation

Adjust this based on your local conditions. You can change it via the dashboard slider.

### Alert Threshold

Set the FDI value that triggers an alert:
- Default: 50 (Severe)
- Adjustable from 1 to 150

### Notifications

Notifications are **disabled by default** as mentioned in requirements. To enable:
1. Toggle "Enable Notifications" ON in the dashboard
2. Currently shows persistent notifications in Home Assistant
3. To enable push notifications, uncomment and configure the mobile notification section in `fire_danger_index.yaml`

## 📱 Enabling Push Notifications (When Ready)

When your push notifications are set up, edit the automation in `fire_danger_index.yaml`:

1. Find the `fire_danger_alert` automation
2. Uncomment the `notify.mobile_app_your_phone` service call
3. Replace `your_phone` with your device name
4. Save and reload automations

```yaml
- service: notify.mobile_app_your_phone
  data:
    title: "🔥 Fire Danger Alert"
    message: >
      Fire Danger Index has reached {{ states('sensor.fire_danger_index') }} 
      ({{ state_attr('sensor.fire_danger_index', 'rating') }}).
```

## 🔧 Troubleshooting

### FDI shows 0 or doesn't update
- Check that your Ecowitt sensors are providing data
- Verify the entity IDs are correct in the template
- Check Developer Tools → States for sensor values

### Graph not showing
- Ensure ApexCharts Card is installed
- Check for JavaScript errors in browser console
- Verify the recorder is tracking the sensor

### History not keeping 3 days
- The recorder `purge_keep_days: 3` setting may conflict with your main recorder config
- You may need to add the sensor to your main recorder include list

## 📁 File Structure

```
homeassistant/
├── fire_danger_index.yaml    # Main automation & sensor package
├── dashboard_card.yaml       # Dashboard card configuration
└── README.md                 # This documentation
```

## 📚 References

- [McArthur Forest Fire Danger Index - Wikipedia](https://en.wikipedia.org/wiki/McArthur_Forest_Fire_Danger_Index)
- [CSIRO - Mk5 Forest Fire Danger Meter](https://www.csiro.au/en/research/disasters/bushfires/Mk5-forest-fire-danger-meter)
- [CFA Victoria](https://www.cfa.vic.gov.au/)
- [ApexCharts Card](https://github.com/RomRider/apexcharts-card)

## 📝 License

This configuration is provided as-is for educational and personal use. The Fire Danger Index is a guideline only - always follow official CFA and emergency service warnings.
