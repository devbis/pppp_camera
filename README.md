# PPPP Camera Component for Home Assistant

## Overview

The `pppp` camera component allows Home Assistant to connect and integrate cheap Wi-Fi cameras such as **A9, X5**, and similar models using the **aiopppp** library. 
These cameras typically use the **Peer-to-Peer protocol** for communication, and this component enables live-streaming and snapshot capture within Home Assistant.

## Features

- Supports A9, X5, and similar PPPP protocol cameras (Only JSON protocol is supported for now)
- Live streaming via aiopppp
- Snapshot support
- PTZ control through actions/services
- White lights and IR lights control
- Support for webrtc custom component
- (TBD) Sound streaming

## Tested camera prefixes

| Prefix   | Protocol | Video | [Audio<sup>*</sup>](https://github.com/devbis/aiopppp/issues/6) | PTZ | White Light | IR Light | Reboot |
|:---------|:---------|:-----:|:---------------------------------------------------------------:|:---:|:-----------:|:--------:|:------:|
| **DGOK** | 📜 JSON  | ✅   | ✖️                                                             | ✅  | ✅          | ✅      | ✅     |
| **PTZA** | 🔢 Binary| ✅   | ✖️                                                             | ✅  | ✅          | 🚫      | ✅     |
| **FTYC** | 🔢 Binary| [❌<sup>*</sup>](https://github.com/devbis/aiopppp/issues/8)| ✖️      | 🚫  | 🚫          | ✅      | ✅     |
| [**BATE**<sup>*</sup>](https://github.com/devbis/pppp_camera/issues/4) | 🔢 Binary|❔ |✖️    | ❔   | ❔           | ❔       | ❔     |
| [**DGB**<sup>*</sup>](https://github.com/devbis/pppp_camera/issues/2) | 📜 JSON   |⚠️ |✖️   | ❔   | ❔           | ❔       | ❔     |
| [**ACCQ**<sup>*</sup>](https://github.com/devbis/pppp_camera/issues/1) | ❔ Unknown|✖️|✖️    | ✖️  | ✖️          | ✖️      | ✖️     |

**Legend:**
- &nbsp;✅&nbsp; **Working**: Feature is fully functional.
- &thinsp;⚠️&thinsp;**Partially working**: Feature works with limitations or issues.
- &nbsp;❌&nbsp; **Not working**: Feature is implemented but does not function.
- &nbsp;✖️&nbsp; **Not implemented**: Feature is not implemented in the system.
- &nbsp;🚫&nbsp; **Not supported**: Feature is not supported by the device.
- &ensp;❔ &nbsp; **Not tested**: Feature has not been tested on the device.

## Installation

### Prerequisites

- Home Assistant installed and running. Tested on version 2025.2

### Installation
1. HACS > Integrations > Custom Repositories
2. Add `devbis/pppp_camera` URL.
3. Select **Integration** as the category.

Or manually copy pppp_camera folder to custom_components folder in your config folder.

## Configuration

Add component and insert camera IP address. If username and passwords are blank it will use default values for 
authentication: `admin:6666`

## Usage

- Once configured, the camera feed should be visible in Home Assistant under **Devices & Services**.
- You can view the stream in **Lovelace UI** by adding a picture entity or a camera card.
- Automations can trigger recordings or snapshots.

PTZ control is available through services e.g.:

```yaml 
action: pppp_camera.ptz
data:
  pan: LEFT
target:
  entity_id: camera.dgok_123456_xxxxx
```


## WebRTC component configuration example:

Component project page: https://github.com/AlexxIT/WebRTC

```yaml
type: custom:webrtc-camera
entity: camera.dgok_123456_xxxxx
media: video
ptz:
  service: pppp_camera.ptz
  data_left:
    pan: LEFT
    entity_id: camera.dgok_123456_xxxxx
  data_right:
    pan: RIGHT
    entity_id: camera.dgok_123456_xxxxx
  data_up:
    tilt: UP
    entity_id: camera.dgok_123456_xxxxx
  data_down:
    tilt: DOWN
    entity_id: camera.dgok_123456_xxxxx

shortcuts:
  - name: White Light
    icon: mdi:lightbulb-on
    service: switch.toggle
    service_data:
      entity_id: switch.dgok_123456_xxxxx_white_lamp
  - name: IR lamp
    icon: mdi:weather-night
    service: switch.toggle
    service_data:
      entity_id: switch.dgok_123456_xxxxx_ir_lamp
```

## Troubleshooting

- **Camera not connecting?** Ensure IP is correct and phone application is not connected. Only one client can connect.
- **No video stream?** Sometimes camera doesn't start streaming. Reboot it.  

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to improve the integration.

## License

This project is licensed under the MIT License.
