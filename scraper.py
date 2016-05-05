import requests, copy, json, math, re, sys
import pickle

fhirbase = 'http://52.72.172.54:8080/fhir/baseDstu2'
fhirheaders = {'Content-Type': 'application/json'}

states = {
    'Mississippi': 'MS', 'Oklahoma': 'OK', 'Delaware': 'DE', 'Minnesota': 'MN', 'Illinois': 'IL', 'Arkansas': 'AR',
    'New Mexico': 'NM', 'Indiana': 'IN', 'Maryland': 'MD', 'Louisiana': 'LA', 'Idaho': 'ID', 'Wyoming': 'WY',
    'Tennessee': 'TN', 'Arizona': 'AZ', 'Iowa': 'IA', 'Michigan': 'MI', 'Kansas': 'KS', 'Utah': 'UT',
    'Virginia': 'VA', 'Oregon': 'OR', 'Connecticut': 'CT', 'Montana': 'MT', 'California': 'CA',
    'Massachusetts': 'MA', 'West Virginia': 'WV', 'South Carolina': 'SC', 'New Hampshire': 'NH',
    'Wisconsin': 'WI', 'Vermont': 'VT', 'Georgia': 'GA', 'North Dakota': 'ND', 'Pennsylvania': 'PA',
    'Florida': 'FL', 'Alaska': 'AK', 'Kentucky': 'KY', 'Hawaii': 'HI', 'Nebraska': 'NE', 'Missouri': 'MO',
    'Ohio': 'OH', 'Alabama': 'AL', 'New York': 'NY', 'South Dakota': 'SD', 'Colorado': 'CO', 'New Jersey': 'NJ',
    'Washington': 'WA', 'North Carolina': 'NC', 'District of Columbia': 'DC', 'Texas': 'TX', 'Nevada': 'NV',
    'Maine': 'ME', 'Rhode Island': 'RI'}
state_abbr = states.values()

#based on JSON example from: https://www.hl7.org/fhir/organization.html
#stripped down to reflect what we really get back from existing FHIR org records.
blank_org = {
    'resourceType' : "Organization",
    # from Resource: id, meta, implicitRules, and language
    # from DomainResource: text, contained, extension, and modifierExtension
    #'identifier' : [{ }], # C? Identifies this organization  across multiple systems
    'active' : True, # Whether the organization's record is still in active use
    'type' : {
        'text': None
    }, # Kind of organization
    'name' : None, # C? Name used for the organization
    #'telecom' : [], # C? A contact detail for the organization
    'address' : [] # C? An address for the organization
}

blank_phone = {
	"system":"phone",
	"value":None,
	"use":"work"
}

def post_org(o):
    """Adds a new community resource org to FHIR server via POST"""
    o_str = json.dumps(o)
    r = requests.post(fhirbase + '/Organization', headers=fhirheaders, data = o_str)
    return r

def delete_org(o_id):
    """Removes a community resource org from FHIR server via DELETE"""
    r = requests.delete(fhirbase + '/Organization/' + o_id, headers=fhirheaders)
    return r

def mapmuse_addr_parse(address):
    """hardcoded parser for mapmuse address format"""
    try:
        aparts = address.split(",")
        addr_line = " ".join(aparts[:-1])
        city_state = aparts[-1].strip()
        city, state = city_state.split(' ', maxsplit=1)
        d = {
	        "line":[addr_line],
	        "city":city,
	        "state":state,
	        "postalCode":None
        }
        return d
    except:
        return None

def mapmuse_to_org(mm, otype):
    """Convert a json object from mapmuse to a fhir organization json object"""
    o = copy.deepcopy(blank_org)
    o['name'] = mm['nam']
    o['type']['text'] = otype
    #no telecom info from mapmuse
    addr = mapmuse_addr_parse(mm['adr'])
    if addr and mm['lat'] and mm['lng']:
        lat = mm['lat']
        lng = mm['lng']
        x = 6370 * math.cos(lat) * math.cos(lng)
        y = 6370 * math.cos(lat) * math.sin(lng)
        z = 6370 * math.sin(lat)
        text_hack = {
            'lat': lat,
            'lng': lng,
            'x': x,
            'y': y,
            'z': z
        }
        addr['text'] = text_hack
    o['address'].append(addr)
    return o

def load_mapmuse(filename, resource_type):
    jlist = json.load(open(filename + ".json", 'r'))
    items = jlist['places']
    orgs = []
    for y in items:
        o = mapmuse_to_org(y, resource_type)
        orgs.append(o)
    return orgs

def add_orgs(load_func, json_file, resource_type):
    print("Starting {0}".format(json_file))
    ys = load_func(json_file, resource_type)
    results = {}
    try:
        for i, y in enumerate(ys):
            if i % 25 == 0:
                print('Adding {0}...'.format(i))
            results[i] = post_org(y)
    except:
        print("Unexpected error:", sys.exc_info()[0])
    finally:
        pickle.dump(results, open(json_file + '_results.pickle', 'wb'))

def remove_orgs(json_file_name):
    results = pickle.load(open(json_file_name + '_results.pickle', 'rb'))
    for r in results.values():
        #extract the id...  response.text is the only place you can get this...
        text = r.text
        #mihin format:
        m = re.search('Successfully created resource \\\\"Organization/(.+?)/_history', r.text)
        #smart on fhir format:
        #m = re.search('<id value=\\"(.+?)\\"', r.text)
        if m:
            id = m.group(1)
            #make a requests call to delete the resource
            print('deleting {0}... '.format(id))
            dr = delete_org(id)
            if dr.status_code == 204:
                print('done.\r\n')
            else:
                print('error: {0}\r\n'.format(dr.status_code))

if __name__ == '__main__':
    pass

    #you can import to fhir from the json files like so:
    #add_orgs(load_mapmuse, 'ymca', "CommunityResource/HealthClub")
    #add_orgs(load_mapmuse, 'health_clubs', "CommunityResource/HealthClub")
    #add_orgs(load_mapmuse, 'playgrounds_nationwide', "CommunityResource/Playground")
    #add_orgs(load_mapmuse, 'rails2trails', "CommunityResource/HikingTrail")

    #you can remove organizations if they errored out halfway through by running:
    #remove_orgs('playgrounds_nationwide')
