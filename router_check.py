''' 
Script to get router information, in both plain text and RRDTool format
Tested only with Zyzel VMG8924-B10A, probably won't work with anything else

## Usage
e.g. Text format (original that router uses)
> python ./router_check.py --text header
    xDSL Training Status:   Showtime
                    Mode:   G.DMT Annex A
            Traffic Type:   ATM Mode
             Link Uptime:   0 day: 22 hours: 9 minutes

e.g. RRDTool Format
> python ./router_check.py --data actual_up actual_down snr_up snr_down
00.448:01.152:25.000:29.300

Requires MechanicalSoup, and Pandas
'''

import argparse
import itertools
from io import StringIO
import sys

import mechanicalsoup
import pandas as pd

USERNAME = "admin"
PASSWORD = "1234"
IP_ADDR = "192.168.1.1"


def is_seperator(line):
    ''' Returns true if a line is a seperator '''
    if len(line) == 0:
        return False
    return line[0] == "="


def split_sections(lines):
    ''' Split lines seperated by ==== bars into groups '''
    # Detect if first element of line is "=" using groupby.
    # "if not x" removes deliminators from output
    return [list(y) for x, y in itertools.groupby(lines,
                                                  is_seperator) if not x]


def extract_sections(status_text):
    ''' Convert status text into dict of section: lines '''
    status_lines = status_text.splitlines()
    sections = split_sections(status_lines)
    _ = sections[0]  # Blank
    # Name each section
    return {
        "header": sections[1],  # Header
        "port": sections[2],  # Upstream/downstream rates
        "counters": sections[3]   # Error counters
    }


def get_router_adsl_status_text(ip_addr):
    ''' Get ADSL status text from router '''
    # Login
    browser = mechanicalsoup.StatefulBrowser()
    browser.open(f"http://{ip_addr}/login/login.html")
    browser.select_form('#login')
    browser["AuthName"] = USERNAME
    browser["AuthPassword"] = PASSWORD
    resp = browser.submit_selected()

    # Error is label for AuthPassword field, actually hidden from show
    # For some reason, tag <label id=Message> <font> $message </font> </label> does not work
    error_msg = resp.soup.find("label", attrs={"for": "AuthPassword"})
    if error_msg:
        print(f"Got \"{error_msg.get_text()}\", so username/password incorrect")
        sys.exit(1)

    # Open new page
    status_page = browser.open(
        f"http://{ip_addr}/pages/systemMonitoring/xdslStatistics/xdslStatistics.html")

    # Find VDSL Status Text element
    status_text = status_page.soup.find(id="VdslInfoDisplay")
    if not status_text:
        raise FileNotFoundError("Could not find VdslInfoDisplay")

    return status_text.text  # Strip HTML wrapper and return


# What the router calls rows in its section. Without "_up" or "_down" suffix
DATA_FIELDS = {
    "line": "Line Rate",
    "actual": "Actual Net Data Rate",
    "snr": "SNR Margin",
    "delay": "Actual Delay",
    "txpower": "Transmit Power",
    "rxpower": "Recieve Power",
    "inp": "Actual INP",
    "attenuation": "Total Attenuation",
    "attainable": "Attainable Net Data Rate"
}

# Convert into options for argparse data section
DATA_CHOICES = [k+"_up" for k in DATA_FIELDS.keys()]
DATA_CHOICES += [k+"_down" for k in DATA_FIELDS.keys()]

# Parse command line args for sections
parser = argparse.ArgumentParser(
    description="Return router ADSL Status, either plain text or for RRD Tool")
group = parser.add_mutually_exclusive_group()
group.add_argument("--text", choices=["header", "port", "counters"],
                   help="Print the plain text from a section/sections",
                   default="port", nargs='+')
group.add_argument("--data", choices=DATA_CHOICES,
                   help="Parse the data from the port section, returned values seperated by colon",
                   nargs="+")
args = parser.parse_args()

# Check a mode has been provided
if not (args.text or args.data):
    parser.error("No action specified, must be either --text or --data")


# Get router text and split into sections
status_text = get_router_adsl_status_text(IP_ADDR)
sections = extract_sections(status_text)

if args.data:
    # Get dataframe from port section, fixed width
    port_stringio = StringIO("\n".join(sections['port']))
    port_df = pd.read_fwf(port_stringio,
                          index_col=0,  # First column is index
                          skipinitialsep=True,  # Remove extra whitespace
                          delimiter=" :"  # Both space and colon are delimiters
                          )

    # Convert to list if only one value given
    if isinstance(args.data, str):
        args.data = [args.data]
    # Return each value
    for n, k in enumerate(args.data):
        if n > 0:
            print(":", end="")  # Add seperator

        # Get correct series, upstream or downstream
        direction = "Upstream" if k.endswith("up") else "Downstream"
        series = port_df[direction]
        # Get row
        row_short_name = k.split("_")[0]  # First section, before _
        row_long_name = DATA_FIELDS[row_short_name]
        data_str = series[row_long_name]
        # Split units off, e.g. "2.00 Mbps" => "2.00" and convert to float
        val = float(data_str.split(" ")[0])
        # Display 6 wide,3dp, zero padded
        print("{:06.3f}".format(val), end='')


elif args.text:  # Default arg
    # If we have only one section, wrap it in a list
    if isinstance(args.text, str):
        args.text = [args.text]
    # Print specified sections
    for k in args.text or []:
        print("\n".join(sections[k]))
