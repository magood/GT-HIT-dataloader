import requests, copy, json, math, re
import pickle

#MiHIN server
fhirbase = 'http://52.72.172.54:8080/fhir/baseDstu2'
fhirheaders = {'Content-Type': 'application/json'}

def delete_org(o_id):
    """Removes a community resource org from FHIR server via DELETE"""
    r = requests.delete(fhirbase + '/Organization/' + o_id, headers=fhirheaders)
    return r

def delete_all_resources():
    next = fhirbase + '/Organization'
    while True:
        response = requests.get(next, headers = fhirheaders)
        orgs = response.json()
        count = orgs['total']
        print("Deleting... {0} to go.".format(count))
    
        hasNext = False
        for l in orgs['link']:
            if l['relation'] == 'next':
                hasNext = True
                next = l['url']

        for o in orgs['entry']:
            type=""
            try:
                type = o['resource']['type']['text']
            except:
                pass
            if type.startswith("CommunityResource/"):
                id = o['resource']['id']
                print('deleting {0}... '.format(id))
                dr = delete_org(id)
                if dr.status_code != 204:
                    print('error deleting {0}: {1}\r\n'.format(id, dr.status_code))
        if not hasNext:
            break

if __name__ == '__main__':
    print("This script deletes all custom community resources from server:\r\n{0}\r\n".format(fhirbase))
    input("Press enter to continue")
    delete_all_resources()