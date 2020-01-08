import sys
import itertools
import mechanicalsoup


USERNAME = "admin"
PASSWORD = "1234"
IP_ADDR  = "192.168.1.1"

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
    _                = sections[0]  # Blank
    # Name each section
    return {
        "header"    : sections[1],  # Header
        "port"      : sections[2],  # Upstream/downstream rates
        "counters"  : sections[3]   # Error counters
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
    error_msg = resp.soup.find("label",attrs={"for": "AuthPassword"})
    if error_msg:
        print(f"Got \"{error_msg.get_text()}\", so username/password incorrect")
        sys.exit(1)

    # Open new page
    status_page = browser.open(f"http://{ip_addr}/pages/systemMonitoring/xdslStatistics/xdslStatistics.html")

    # Find VDSL Status Text element
    status_text = status_page.soup.find(id="VdslInfoDisplay")
    if not status_text:
        raise FileNotFoundError("Could not find VdslInfoDisplay")

    return status_text.text # Strip HTML wrapper and return


status_text = get_router_adsl_status_text(IP_ADDR)
sections = extract_sections(status_text)
print("\n".join(sections['header']))
    
