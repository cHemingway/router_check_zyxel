# router_check_zyxel
Script to get router information, in both plain text and RRDTool format

Tested only with Zyzel VMG8924-B10A, probably won't work with anything else
### Usage
#### Text format (original that router uses)
```
> python ./router_check.py --text header
    xDSL Training Status:   Showtime
                    Mode:   G.DMT Annex A
            Traffic Type:   ATM Mode
             Link Uptime:   0 day: 22 hours: 9 minutes
```
#### RRDTool Format
> python ./router_check.py --data actual_up actual_down snr_up snr_down
00.448:01.152:25.000:29.300

### Requires
- [MechanicalSoup](https://mechanicalsoup.readthedocs.io)
- Pandas
- Python >=3.7
