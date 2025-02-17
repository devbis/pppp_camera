# pppp Camera Component for Home Assistant

## Overview

The `pppp` camera component allows Home Assistant to connect and integrate cheap Wi-Fi cameras such as **A9, X5**, and similar models using the **aiopppp** library. 
These cameras typically use the **Peer-to-Peer protocol** for communication, and this component enables live-streaming and snapshot capture within Home Assistant.

## Features

- Supports A9, X5, and similar PPPP protocol cameras
- Live streaming via aiopppp
- Snapshot support
- Integration with Home Assistant dashboards

## Tested camera prefixes

- DGOK*

## Installation

### Prerequisites

- Home Assistant installed and running
- Python 3.9+

### Installation
1. HACS > Integrations > Custom Repositories
2. Add `devbis/pppp_camera` URL.
3. Select **Integration** as the category.

Or manually copy pppp_camera folder to custom_components folder in your config folder.

## Configuration

Add component and insert camera IP address

## Usage

- Once configured, the camera feed should be visible in Home Assistant under **Devices & Services**.
- You can view the stream in **Lovelace UI** by adding a picture entity or a camera card.
- Automations can trigger recordings or snapshots.

## Troubleshooting

- **Camera not connecting?** Ensure IP is correct and phone application is not connected. Only one client can connect.
- **No video stream?** Sometimes camera doesn't start streaming. Reboot it.  
- 
## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to improve the integration.

## License

This project is licensed under the MIT License.
