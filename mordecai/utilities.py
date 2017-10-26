# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
import os
import sys
import json
import numpy
import mitie
import pprint
import argparse
import pandas as pd
from elasticsearch_dsl import Search, Q
from elasticsearch import Elasticsearch

import spacy
nlp = spacy.load('en_core_web_lg')


def parse_args():
    parser = argparse.ArgumentParser(description='Mordecai Geolocation')
    parser._optionals.title = 'Options'
    parser.add_argument('-c', '--config-file',
                        help='Specify path to config file.',
                        type=str,
                        required=False,
                        default="")
    parser.add_argument('-p', '--port',
                        help='Specify port to listen on.',
                        type=int,
                        required=False,
                        default=5000)
    parser.add_argument('-eh', '--elasticsearch-host',
                        help='Specify elasticsearch host.',
                        type=str,
                        required=False,
                        default='elastic')
    parser.add_argument('-ep', '--elasticsearch-port',
                        help='Specify elasticsearch port.',
                        type=str,
                        required=False,
                        default='9200')
    parser.add_argument('-w', '--w2v-model',
                        help='Specify path to w2v model.',
                        type=str,
                        required=False,
                        default="/usr/src/data/GoogleNews-vectors-negative300.bin.gz")
    parser.add_argument('-md', '--mitie-dir',
                        help='Specify MITIE directory.',
                        type=str,
                        required=False,
                        default="/usr/src/MITIE/mitielib")
    parser.add_argument('-mn', '--mitie-ner',
                        help='Specify path to MITIE NER model.',
                        type=str,
                        required=False,
                        default="/usr/src/data/MITIE-models/english/ner_model.dat")
    return parser.parse_args()


def country_list_maker():
    cts = {"Afghanistan":"AFG", "Åland Islands":"ALA", "Albania":"ALB", "Algeria":"DZA",
    "American Samoa":"ASM", "Andorra":"AND", "Angola":"AGO", "Anguilla":"AIA",
    "Antarctica":"ATA", "Antigua Barbuda":"ATG", "Argentina":"ARG",
    "Armenia":"ARM", "Aruba":"ABW", "Ascension Island":"NA", "Australia":"AUS",
    "Austria":"AUT", "Azerbaijan":"AZE", "Bahamas":"BHS", "Bahrain":"BHR",
    "Bangladesh":"BGD", "Barbados":"BRB", "Belarus":"BLR", "Belgium":"BEL",
    "Belize":"BLZ", "Benin":"BEN", "Bermuda":"BMU", "Bhutan":"BTN",
    "Bolivia":"BOL", "Bosnia Herzegovina":"BIH",
    "Botswana":"BWA", "Bouvet Island":"BVT", "Brazil":"BRA",
    "Britain":"GBR", "Great Britain":"GBR",
    "British Virgin Islands":"VGB", "Brunei":"BRN", "Bulgaria":"BGR", "Burkina Faso":"BFA",
    "Burundi":"BDI", "Cambodia":"KHM", "Cameroon":"CMR",
    "Canada":"CAN","Cape Verde":"CPV", "Cayman Islands":"CYM",
    "Central African Republic":"CAF", "Chad":"TCD", "Chile":"CHL", "China":"CHN",
    "Cocos Islands":"CCK", "Colombia":"COL",
    "Comoros":"COM", "Congo Brazzaville":"COG", "Congo Kinshasa":"COD",
    "Congo":"COG", "Cook Islands":"COK",
    "Costa Rica":"CRI", "Cote Ivoire":"CIV", "Ivory Coast":"CIV","Croatia":"HRV", "Cuba":"CUB",
    "Curaçao":"CUW", "Cyprus":"CYP", "Czech Republic":"CZE", "Denmark":"DNK",
    "Djibouti":"DJI", "Dominica":"DMA", "Dominican Republic":"DOM", "Democratic Republic of Congo" : "COD",
    "Ecuador":"ECU", "Egypt":"EGY", "El Salvador":"SLV", "England" : "GBR",
    "Equatorial Guinea":"GNQ", "Eritrea":"ERI", "Estonia":"EST", "Ethiopia":"ETH",
    "Falkland Islands":"FLK", "Faroe Islands":"FRO",
    "Fiji":"FJI", "Finland":"FIN", "France":"FRA", "French Guiana":"GUF",
    "French Polynesia":"PYF","Gabon":"GAB",
    "Gambia":"GMB", "Georgia":"GEO", "Germany":"DEU", "Ghana":"GHA",
    "Gibraltar":"GIB", "Greece":"GRC", "Greenland":"GRL", "Grenada":"GRD",
    "Guadeloupe":"GLP", "Guam":"GUM", "Guatemala":"GTM", "Guernsey":"GGY",
    "Guinea":"GIN", "Guinea Bissau":"GNB", "Guyana":"GUY", "Haiti":"HTI","Honduras":"HND",
    "Hong Kong":"HKG",  "Hungary":"HUN", "Iceland":"ISL",
    "India":"IND", "Indonesia":"IDN", "Iran":"IRN", "Iraq":"IRQ", "Ireland":"IRL",
    "Israel":"ISR", "Italy":"ITA", "Jamaica":"JAM", "Japan":"JPN",
    "Jordan":"JOR", "Kazakhstan":"KAZ", "Kenya":"KEN",
    "Kiribati":"KIR", "Kosovo": "KSV", "Kuwait":"KWT", "Kyrgyzstan":"KGZ", "Laos":"LAO",
    "Latvia":"LVA", "Lebanon":"LBN", "Lesotho":"LSO", "Liberia":"LBR",
    "Libya":"LBY", "Liechtenstein":"LIE", "Lithuania":"LTU", "Luxembourg":"LUX",
    "Macau":"MAC", "Macedonia":"MKD", "Madagascar":"MDG", "Malawi":"MWI",
    "Malaysia":"MYS", "Maldives":"MDV", "Mali":"MLI", "Malta":"MLT", "Marshall Islands":"MHL",
    "Martinique":"MTQ", "Mauritania":"MRT", "Mauritius":"MUS",
    "Mayotte":"MYT", "Mexico":"MEX", "Micronesia":"FSM", "Moldova":"MDA",
    "Monaco":"MCO", "Mongolia":"MNG", "Montenegro":"MNE", "Montserrat":"MSR",
    "Morocco":"MAR", "Mozambique":"MOZ", "Myanmar":"MMR", "Burma":"MMR", "Namibia":"NAM",
    "Nauru":"NRU", "Nepal":"NPL", "Netherlands":"NLD", "Netherlands Antilles":"ANT",
    "New Caledonia":"NCL", "New Zealand":"NZL", "Nicaragua":"NIC",
    "Niger":"NER", "Nigeria":"NGA", "Niue":"NIU", "North Korea":"PRK",
    "Northern Ireland":"IRL", "Northern Mariana Islands":"MNP",
    "Norway":"NOR", "Oman":"OMN", "Pakistan":"PAK",
    "Palau":"PLW", "Palestinian Territories":"PSE", "Palestine":"PSE","Panama":"PAN", "Papua New Guinea":"PNG",
    "Paraguay":"PRY", "Peru":"PER", "Philippines":"PHL", "Pitcairn Islands":"PCN",
    "Poland":"POL", "Portugal":"PRT", "Puerto Rico":"PRI",
    "Qatar":"QAT", "Réunion":"REU", "Romania":"ROU", "Russia":"RUS",
    "Rwanda":"RWA", "Saint Barthélemy":"BLM", "Saint Helena":"SHN",
    "Saint Kitts Nevis":"KNA", "Saint Lucia":"LCA",
    "Saint Pierre Miquelon":"SPM", "Saint Vincent Grenadines":"VCT",
    "Samoa":"WSM", "San Marino":"SMR", "São Tomé Príncipe":"STP", "Saudi Arabia":"SAU",
    "Senegal":"SEN", "Serbia":"SRB",
    "Seychelles":"SYC", "Sierra Leone":"SLE", "Singapore":"SGP", "Sint Maarten":"SXM",
    "Slovakia":"SVK", "Slovenia":"SVN", "Solomon Islands":"SLB",
    "Somalia":"SOM", "South Africa":"ZAF",
    "South Korea":"KOR", "South Sudan":"SSD", "Spain":"ESP", "Sri Lanka":"LKA", "Sudan":"SDN",
    "Suriname":"SUR", "Svalbard Jan Mayen":"SJM",
    "Swaziland":"SWZ", "Sweden":"SWE", "Switzerland":"CHE", "Syria":"SYR",
    "Taiwan":"TWN", "Tajikistan":"TJK", "Tanzania":"TZA", "Thailand":"THA",
    "Timor Leste":"TLS", "East Timor":"TLS","Togo":"TGO", "Tokelau":"TKL", "Tonga":"TON", "Trinidad Tobago":"TTO",
    "Tunisia":"TUN", "Turkey":"TUR",
    "Turkmenistan":"TKM", "Turks Caicos Islands":"TCA", "Tuvalu":"TUV", "U.S. Minor Outlying Islands":"UMI",
    "Virgin Islands":"VIR", "Uganda":"UGA",
    "Ukraine":"UKR", "United Arab Emirates":"ARE", "United Kingdom":"GBR",
    "UK":"GBR", "United States":"USA", "USA":"USA", "America":"USA",
    "Uruguay":"URY", "Uzbekistan":"UZB", "Vanuatu":"VUT", "Vatican":"VAT", "Venezuela":"VEN",
    "Vietnam":"VNM", "Wallis Futuna":"WLF",
    "Western Sahara":"ESH", "Yemen":"YEM", "Zambia":"ZMB", "Zimbabwe":"ZWE",
    "New York" : "USA", "Maine" : "USA", "Oklahoma" : "USA", "Atlanta" : "USA", "Washington" : "USA",
    "California" : "USA", "Chicago" : "USA", "Illinois" : "USA", "Beijing" : "CHN",
    "Tbilisi" : "GEO", "Gaza":"PSE",}
    return cts

def make_skip_list(cts):
    special_terms = ["Europe", "West", "the West", "South Pacific", "Gulf of Mexico", "Atlantic",
                    "the Black Sea", "Black Sea", "North America", "Mideast", "Middle East",
                     "the Middle East", "Asia", "the Caucasus", "Africa",
                    "Central Asia", "Balkans", "Eastern Europe", "Arctic", "Ottoman Empire",
                    "Asia-Pacific", "East Asia", "Horn of Africa", "Americas",
                    "North Africa", "the Strait of Hormuz", "Mediterranean", "East", "North",
                     "South", "Latin America", "Southeast Asia", "Western Pacific", "South Asia",
                    "Persian Gulf", "Central Europe", "Western Hemisphere", "Western Europe",
                    "European Union (E.U.)", "EU", "European Union", "E.U.", "Asia-Pacific",
                 "Europe", "Caribbean"
                ]

    # maybe remove these? Sometimes they mean something, though "Northwest Provice"
    other = ["Northeast"]

    skip_list = list(cts.keys()) + special_terms
    skip_list = set(skip_list)
    return skip_list


def country_list_nlp(cts):
    ct_nlp = []
    for i in cts.keys():
        nlped = nlp(i)
        ct_nlp.append(nlped)
    return ct_nlp


def make_country_nationality_list(cts):
    ct_file = "nat_df.csv"
    countries = pd.read_csv(ct_file)
    nationality = dict(zip(countries.nationality,countries.alpha_3_code))
    both_codes = {**nationality, **cts}
    return both_codes


def make_inv_cts(cts):
    inv_ct = {}
    for old_k, old_v in cts.items():
        if old_v not in inv_ct.keys():
            inv_ct.update({old_v : old_k})
    return inv_ct


def read_in_admin1(filepath):
    """
    Small helper function to read in a admin1 code <--> admin1 name document.
    Parameters
    ----------
    filepath: string
              path to the admin1 mapping JSON. This file is usually
              mordecai/resources/data/admin1CodesASCII.json
    Returns
    -------
    admin1_dict: dictionary
                 keys are country + admin1codes, values are names
                 Example: "US.OK" : "Oklahoma"
                 Example: "SE.21": "Uppsala"
    """
    with open(filepath) as admin1file:
        admin1_dict = json.loads(admin1file.read())
    return admin1_dict


def get_admin1(country_code2, admin1_code, admin1_dict):
    """
    Convert a geonames admin1 code to the associated place name.
    Parameters
    ---------
    country_code2: string
                   The two character country code
    admin1_code: string
                 The admin1 code to be converted. (Admin1 is the highest
                 subnational political unit, state/region/provice/etc.
    admin1_dict: dictionary
                 The dictionary containing the country code + admin1 code
                 as keys and the admin1 names as values.
    Returns
    ------
    admin1_name: string
                 The admin1 name. If none is found, return "NA".
    """
    lookup_key = ".".join([country_code2, admin1_code])
    try:
        admin1_name = admin1_dict[lookup_key]
        return admin1_name
    except KeyError:
        m = "No admin code found for country {} and code {}".format(country_code2, admin1_code)
        print(m)
        return "NA"

def structure_results(res):
    out = {'hits': {'hits': []}}
    keys = [u'admin1_code', u'admin2_code', u'admin3_code', u'admin4_code',
            u'alternativenames', u'asciiname', u'cc2', u'coordinates',
            u'country_code2', u'country_code3', u'dem', u'elevation',
            u'feature_class', u'feature_code', u'geonameid',
            u'modification_date', u'name', u'population', u'timezone']
    for i in res:
        i_out = {}
        for k in keys:
            i_out[k] = i[k]
        out['hits']['hits'].append(i_out)
    return out

def setup_es(es_ip, es_port):
    """
    Setup an Elasticsearch connection
    Parameters
    ----------
    es_ip: string
            IP address for elasticsearch instance
    es_port: string
            Port for elasticsearch instance
    Returns
    -------
    es_conn: an elasticsearch_dsl Search connection object.
    """
    CLIENT = Elasticsearch([{'host' : es_ip, 'port' : es_port}])
    S = Search(using=CLIENT, index="geonames")
    return S