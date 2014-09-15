#!/usr/bin/python
import sys,json, requests,datetime,xdg.BaseDirectory
from requests.auth import HTTPBasicAuth
from types import *
import argparse
import os.path
from configobj import ConfigObj

# You will need to get the access token from github for authorization to use the API to post
# Access token is considered a "secret" akin to a password so... you know...be careful with this script
# This script will read a token string from a file on system
# If set prefer command line argument else
# If set use environment variable else
# default to using $XDG_CONFIG_HOME/github_release_script/owner_repo.token
# token file should be treated as sensitive secrets file and permissions should be restricted as narrowly as possible.
access_token=None

# End configuration
parser = argparse.ArgumentParser(description='Generate Github release')
parser.add_argument('-o','--owner'    , required=False  , help='github account',default="vtsuperdarn")
parser.add_argument('-r','--repo'     ,  required=False , help='repository',default="hdw.dat")
parser.add_argument('-b','--branch'   ,required=False   , help='branch',default="master" )
parser.add_argument('-p','--path'     ,required=False   , help='path to token file store' )
parser.add_argument('-t','--tokenfile',required=False   , help='token filename' )
parser.add_argument('-m','--message',  required=False   , help='optional release message' )
parser.add_argument('-v','--verbose'  ,required=False   , help='turn on diagnostic output', action='store_true')
parser.add_argument('-q','--quiet'    ,required=False   , help='turn off all output', action='store_true')
parser.add_argument('--run'           ,required=False   , help='generate release', action='store_true')
parser.add_argument('--draft'         ,required=False   , help='Mark as draft', action='store_true')
parser.add_argument('--force'         ,required=False   , help='Force release generation', action='store_true')
parser.add_argument('--prerelease'    ,required=False   , help='Mark as prerelease', action='store_true')
args=parser.parse_args()

#Reset draft and prerelease args to lower case for json consumption
args.draft="{0}".format(args.draft).lower()
args.prerelease="{0}".format(args.prerelease).lower()
print args
sys,exit(0)
# Setup Path 
if args.path is None:
  args.path=xdg.BaseDirectory.save_config_path("github_release_script")
if args.verbose: print "Using Config path:", args.path
if not os.path.isdir(args.path):
  if not args.quiet: print "Warning: {0:s} does not appear to be a valid directory".format(args.path)  
# Setup file
if args.tokenfile is None:
  args.tokenfile="{0:s}_{1:s}.token".format(args.owner,args.repo)
if (args.verbose): print "Using Token file:", args.tokenfile
filepath=os.path.join(args.path,args.tokenfile)
if not os.path.isfile(filepath):
  if not args.quiet: print "Warning: {0:s} does not appear to be a valid file".format(filepath)  
if args.verbose: print "opening: {0:s}".format(filepath)
config = ConfigObj(filepath)
access_token=config.get('access_token') 
if args.verbose: print "Using access token:",access_token

assert type(access_token) is StringType,\
  "Must set access_token variable to a valid token string as issued by github for your account"

now=datetime.datetime.utcnow()
tagdatestr="v{0:04d}{1:02d}{2:02d}".format(now.year,now.month,now.day)
max_rev=0

url = 'https://api.github.com/repos/{0:s}/{1:s}/commits'.format(args.owner,args.repo)
resp = requests.get(url=url)
assert resp.status_code == requests.codes.ok,\
  "Get commits request to: {0:s} failed with Http response status: {1:d}".format(url,resp.status_code)
last_item = json.loads(resp.text)[0]
last_commit_sha=last_item["sha"]
if args.verbose:
  print "Last Commit sha: {0:s}".format(last_commit_sha)
 
url = 'https://api.github.com/repos/{0:s}/{1:s}/tags'.format(args.owner,args.repo)
resp = requests.get(url=url)
assert resp.status_code == requests.codes.ok,\
  "Get request to: {0:s} failed with Http response status: {1:d}".format(url,resp.status_code)
data = json.loads(resp.text)

abort_generation=False
if args.verbose:
  print "Checking for existing release tags"
for item in data:
  tag=item["name"]
  commit=item["commit"]
  if args.verbose: print "  {0:s} : commit sha: {1:s}".format(tag,commit["sha"])
  if commit["sha"]==last_commit_sha:
    if not args.force: 
      if args.verbose: print "    {0:s} matches last commit\n".format(tag)
      abort_generation=True
  tag_elements=tag.split(".")
  # First lets make sure we aren't tagging in the past!!!!!
  assert int(tag_elements[0].decode()[1:]) <= int(tagdatestr[1:]),\
    "Current UTC date {1} is older than existing tag {0:s}!".format(tag,now.date())

  if tagdatestr == tag_elements[0].decode():
    max_rev=max(max_rev,int(tag_elements[1].decode()))
max_rev=max_rev+1
new_tag="{0:s}.{1:d}".format(tagdatestr,max_rev)
if args.message is None:
  args.message="Release of version {0:s}".format(new_tag)
API_JSON='{{\n"tag_name": "{0:s}",\n"target_commitish": "{1:s}",\n"name": "{0:s}",\n"body": "{2:s}",\n"draft": {3:s},\n"prerelease": {4:s}\n}}'.format(new_tag,args.branch,args.message,args.draft,args.prerelease)
if args.verbose:
  print "github JSON payload for requested release:"
  print API_JSON
if abort_generation:
  if not args.quiet: print "Warning: Release generation aborted due to existing release commit match\n  Use --force option to force release generation"
else: 
  if args.run:
    payload = API_JSON
    url = 'https://api.github.com/repos/{0:s}/{1:s}/releases'.format(args.owner,args.repo)
    resp = requests.post(url=url, data=payload,auth=HTTPBasicAuth(access_token, "x-oauth-basic"))
    assert resp.status_code == requests.codes.created,\
      "Post request to: {0:s} failed with Http response status: {1:d}".format(url,resp.status_code)
  else:
    if not args.quiet: print "Notice: script dryrun only. No release will be generated. Must use cmdline option --run to create release on github"
