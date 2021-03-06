# Tuya Local Integration [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)


This is a custom component for home assistant to integrate Tuya switch device locally. 

## Requirements

1. device id 
1. local key of the device

## Install 

This custom component supports both HACS and legacy custom componennts methods. 

##### HACS 

1. Navigate to HACS
1. Choose "Integrations"
1. Choose "Custom repositories" from the menu at top right of the window
1. Add this repository url to "Add custom repository URL" 
1. Choose "Integration" for "Category"
1. Click "Add" 
1. Find "Tuya Local" and click "Install"

##### Legacy Method

1. Download the files
1. Copy the folder "custom_components/tuyalocal"  to your config folder


## Setup

This component supports config flow, so you can either configure it in configuration.yaml or add from frontend "Configuration -> Integrations"

##### YAML

```yaml
switch:
  - platform: localtuya
    host: 192.168.10.122  # (required) ip addres of the device
    local_key: !secret local_key  # (required) local key of the device
    device_id: !secret device_id  # (required) device id 
    update_interval: 10 # (optional) frequency to update the status in seconds, default: 10
    current: 5  # (optional) attribute id for current
    current_consumption: 6 #(optional) attribute id for current consumption
    voltage: 7 #(optional) attribute id for voltage
    switches: # (optional) 
      switch1:
        friendly_name: tuya switch restroom
        id: 1

```
_**update_interval** is different from **scan_interval**, this value limits the frequency between updates of a tuya device. Default value is 10, generally 3 seconds works fine._ 

##### Frontend Integration

1. Navigate to "Configuration -> Integrations"
1. Click "+" in "Integrations" tab
1. Enter "Tuya Local" in the search box and click to start configuration



Credits: Thanks to [@mileperhour](https://github.com/mileperhour/localtuya-homeassistant) for all the work.