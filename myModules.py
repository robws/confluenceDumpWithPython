import requests
import os.path
import json
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup as bs
import sys
import pypandoc
from PIL import Image
import re

"""
Arguments needed to run these functions centrally:
* outdirs: outdir, attach_dir, emoticonDir, styles_dir
* page details: Title, ID, Parent, orig URL, Space
* space details: Title, ID, site
* Confluence API: Username, Password

CURRENT STATE
* fixed getting output folders
* next up: getAttachments

"""
#
# Set path for where script is
#
script_dir = os.path.dirname(os.path.abspath(__file__))
attach_dir = "_images/"
emoticons_dir = "_images/"
styles_dir = "_static/"

def set_variables():
    dict_vars = {}
    dict_vars['attach_dir'] = "_images/"
    dict_vars['emoticons_dir'] = "_images/"
    dict_vars['styles_dir'] = "_static/"
    attach_dir = "_images/"
    emoticons_dir = "_images/"
    styles_dir = "_static/"
    return(dict_vars)
#
# Create the output folders, set to match Sphynx structure
#
def set_dirs(arg_outdir="output"):        # setting default to output
    my_vars = set_variables()
    outdir_attach = os.path.join(arg_outdir,my_vars['attach_dir'])
    outdir_emoticons = os.path.join(arg_outdir,my_vars['emoticons_dir'])
    outdir_styles = os.path.join(arg_outdir,my_vars['styles_dir'])
    return[outdir_attach, outdir_emoticons, outdir_styles]      # returns a list

def mk_outdirs(arg_outdir="output"):       # setting default to output
    my_vars = set_variables()
    outdir_list = set_dirs(arg_outdir)
    outdir_attach = outdir_list[0]
    outdir_emoticons = outdir_list[1]
    outdir_styles = outdir_list[2]

    if not os.path.exists(arg_outdir):
        os.mkdir(arg_outdir)

    if not os.path.exists(outdir_attach):
        os.mkdir(outdir_attach)

    if not os.path.exists(outdir_emoticons):
        os.mkdir(outdir_emoticons)

    if not os.path.exists(outdir_styles):
        os.mkdir(outdir_styles)

    if not os.path.exists(outdir_styles + '/confluence.css'):
        os.system('cp ' + script_dir + '/styles/confluence.css "' + outdir_styles + '"')
    return(outdir_list)

def get_space_title(arg_site,arg_space_id,arg_username,arg_api_token):
    server_url = 'https://' + arg_site + '.atlassian.net/wiki/api/v2/spaces/' + str(arg_space_id)
    response = requests.get(server_url, auth=(arg_username, arg_api_token),timeout=30).json()['name']
    return(response)

def get_spaces_all(arg_site,arg_username,arg_api_token):
    #space_list = []
    server_url = 'https://' + arg_site + '.atlassian.net/wiki/api/v2/spaces/?limit=250'
    response = requests.get(server_url, auth=(arg_username,arg_api_token),timeout=30)
    response.raise_for_status()  # raises exception when not a 2xx response
    space_list = response.json()['results']
    while 'next' in response.json()['_links'].keys():
        #print(str(response.json()['_links']))
        cursorserver_url = server_url + '&cursor' + response.json()['_links']['next'].split('cursor')[1]
        #print(server_url)
        response = requests.get(cursorserver_url, auth=(arg_username,arg_api_token),timeout=30)
        space_list = space_list + response.json()['results']
    return(space_list)

def get_pages_from_space(arg_site,arg_space_id,arg_username,arg_api_token):
    page_list = []
    server_url = 'https://' + arg_site + '.atlassian.net/wiki/api/v2/spaces/' + str(arg_space_id) + '/pages?status=current&limit=250'
    response = requests.get(server_url, auth=(arg_username,arg_api_token),timeout=30)
    page_list = response.json()['results']
    while 'next' in response.json()['_links'].keys():
        #@çprint(str(response.json()['_links']))
        cursorserver_url = server_url + '&cursor' + response.json()['_links']['next'].split('cursor')[1]
        response = requests.get(cursorserver_url, auth=(arg_username,arg_api_token),timeout=30)
        page_list = page_list + response.json()['results']
    return(page_list)

def get_body_export_view(arg_site,arg_page_id,arg_username,arg_api_token):
    server_url = 'https://' + arg_site + '.atlassian.net/wiki/rest/api/content/' + str(arg_page_id) + '?expand=body.export_view'
    response = requests.get(server_url, auth=(arg_username, arg_api_token))
    return(response)

def get_page_name(arg_site,arg_page_id,arg_username,arg_api_token):
    server_url = 'https://' + arg_site + '.atlassian.net/wiki/rest/api/content/' + str(arg_page_id)
    r_pagetree = requests.get(server_url, auth=(arg_username, arg_api_token),timeout=30)
    return(r_pagetree.json()['id'] + "_" + r_pagetree.json()['title'])

def get_page_parent(arg_site,arg_page_id,arg_username,arg_api_token):
    server_url = 'https://' + arg_site + '.atlassian.net/wiki/api/v2/pages/' + str(arg_page_id)
    response = requests.get(server_url, auth=(arg_username, arg_api_token),timeout=30)
    return(response.json()['parentId'])

def get_attachments(arg_site,arg_page_id,arg_outdir_attach,arg_username,arg_api_token):
    my_attachments_list = []
    server_url = 'https://' + arg_site + '.atlassian.net/wiki/rest/api/content/' + str(arg_page_id) + '?expand=children.attachment'
    response = requests.get(server_url, auth=(arg_username, arg_api_token),timeout=30)
    my_attachments = response.json()['children']['attachment']['results']
    for attachment in my_attachments:
        attachment_title = requests.utils.unquote(attachment['title']).replace(" ","_").replace(":","-")         # I want attachments without spaces
        print("Downloading: " + attachment_title)
        #attachment_title = n['title']
        #attachment_title = attachment_title.replace(":","-").replace(" ","_").replace("%20","_")          # replace offending characters from file name
        #myTail = n['_links']['download']
        attachment_url = 'https://' + arg_site + '.atlassian.net/wiki' + attachment['_links']['download']
        request_attachment = requests.get(attachment_url, auth=(arg_username, arg_api_token),allow_redirects=True,timeout=30)
        file_path = os.path.join(arg_outdir_attach,attachment_title)
        #if (request_attachment.content.decode("utf-8")).startswith("<!doctype html>"):
        #    file_path = str(file_path) + ".html"
        open(os.path.join(arg_outdir_attach,attachment_title), 'wb').write(request_attachment.content)
        my_attachments_list.append(attachment_title)
    return(my_attachments_list)

# get page labels
def get_page_labels(arg_site,arg_page_id,arg_username,arg_api_token):
    html_labels = []
    server_url = 'https://' + arg_site + '.atlassian.net/wiki/api/v2/pages/' + str(arg_page_id) + '/labels'
    response = requests.get(server_url, auth=(arg_username,arg_api_token),timeout=30).json()
    for l in response['results']:
        html_labels.append(l['name'])
    html_labels = ",".join(html_labels)
    return(html_labels)

def get_page_properties_children(arg_site,arg_html,arg_outdir,arg_username,arg_api_token):
    my_page_properties_children = []
    my_page_properties_children_dict = {}
    soup = bs(arg_html, "html.parser")
    my_page_properties_items = soup.findAll('td',class_="title")
    my_page_properties_items_counter = 0
    for n in my_page_properties_items:
        my_page_id = str(n['data-content-id'])
        my_page_properties_children.append(str(n['data-content-id']))
        my_page_properties_items_counter = my_page_properties_items_counter + 1
        my_page_name = get_page_name(arg_site,int(my_page_id),arg_username,arg_api_token).rsplit('_',1)[1].replace(":","-").replace(" ","_").replace("%20","_")          # replace offending characters from file name
        my_page_properties_children_dict.update({ my_page_id:{}})
        my_page_properties_children_dict[my_page_id].update({"ID": my_page_id})
        my_page_properties_children_dict[my_page_id].update({"Name": my_page_name})
    print(str(my_page_properties_items_counter) + " Page Properties Children Pages")
    #print("Exporting to: " + arg_outdir)
    return[my_page_properties_children,my_page_properties_children_dict]


def dump_html(arg_site,arg_html,arg_title,arg_page_id,arg_outdir_base,arg_outdir_content,arg_page_labels,arg_page_parent,arg_username,arg_api_token,arg_sphinx_compatible=True,arg_type="common"):
    my_vars = set_variables()
    my_emoticons_list = []
    my_outdir_content = arg_outdir_content
    #my_outdir_content = os.path.join(arg_outdir_base,str(arg_page_id) + "-" + str(arg_title))      # this is for html and rst files
    if not os.path.exists(my_outdir_content):
        os.mkdir(my_outdir_content)
    #myOutdir = os.path.join(arg_outdir,str(arg_page_id) + "-" + str(arg_title))
    my_outdirs = mk_outdirs(arg_outdir_base)        # this is for everything for _images and _static
    my_vars = set_variables()     # create a dict with the 3 folder paths: attach, emoticons, styles

    soup = bs(arg_html, "html.parser")
    html_file_name = str(arg_title) + '.html'
    html_file_path = os.path.join(my_outdir_content,html_file_name)
    my_attachments = get_attachments(arg_site,arg_page_id,str(my_outdirs[0]),arg_username,arg_api_token)
    #
    # used for pageprops mode
    #
    #if (arg_type == "child"):
        #my_report_children_dict = get_page_properties_children(arg_site,arg_html,arg_outdir,arg_username,arg_api_token)[1]              # get list of all page properties children
        #my_report_children_dict[arg_page_id].update({"Filename": arg_html_file_name})
    if (arg_type == "report"):
        my_report_children_dict= get_page_properties_children(arg_site,arg_html,my_outdir_content,arg_username,arg_api_token)[1]      # dict
        my_page_properties_items = soup.findAll('td',class_="title")       # list
        for item in my_page_properties_items:
            id = item['data-content-id']
            item.a['href'] = (my_report_children_dict[id]['Name'] + '.html')
    #
    # dealing with "confluence-embedded-image confluence-external-resource"
    #
    my_embeds_externals = soup.findAll('img',class_="confluence-embedded-image confluence-external-resource")
    my_embeds_externals_counter = 0
    for embed_ext in my_embeds_externals:
        orig_embed_external_path = embed_ext['src']     # online link to file
        orig_embed_external_name = orig_embed_external_path.rsplit('/',1)[-1].rsplit('?')[0]      # just the file name
        my_embed_external_name = str(arg_page_id) + "-" + str(my_embeds_externals_counter) + "-" + requests.utils.unquote(orig_embed_external_name).replace(" ", "_").replace(":","-")    # local filename
        my_embed_external_path = os.path.join(my_outdirs[0],my_embed_external_name)        # local filename and path
        if arg_sphinx_compatible == True:
            my_embed_external_path_relative = os.path.join(str('../' + my_vars['attach_dir']),my_embed_external_name)
        else:
            my_embed_external_path_relative = os.path.join(my_vars['attach_dir'],my_embed_external_name)
        to_download = requests.get(orig_embed_external_path, allow_redirects=True)
        try:
            open(my_embed_external_path,'wb').write(to_download.content)
        except:
            print(orig_embed_external_path)
        img = Image.open(my_embed_external_path)
        if img.width < 600:
            embed_ext['width'] = img.width
        else:
            embed_ext['width'] = 600
        img.close
        embed_ext['height'] = "auto"
        embed_ext['onclick'] = "window.open(\"" + str(my_embed_external_path_relative) + "\")"
        embed_ext['src'] = str(my_embed_external_path_relative)
        embed_ext['data-image-src'] = str(my_embed_external_path_relative)
        my_embeds_externals_counter = my_embeds_externals_counter + 1

    #
    # dealing with "confluence-embedded-image"
    #
    my_embeds = soup.findAll('img',class_=re.compile("^confluence-embedded-image"))
    print(str(len(my_embeds)) + " embedded images.")
    for embed in my_embeds:
        orig_embed_path = embed['src']        # online link to file
        orig_embed_name = orig_embed_path.rsplit('/',1)[-1].rsplit('?')[0]      # online file name
        my_embed_name = requests.utils.unquote(orig_embed_name).replace(" ", "_")    # local file name
        my_embed_path = my_outdirs[0] + my_embed_name                            # local file path
        if arg_sphinx_compatible == True:
            my_embed_path_relative = '../' + my_vars['attach_dir'] + my_embed_name
        else:
            my_embed_path_relative = my_vars['attach_dir'] + my_embed_name
        try:
            img = Image.open(my_embed_path)
        except:
            print("WARNING: Skipping embed file " + my_embed_path + " due to issues.")
        else:
            if img.width < 600:
                embed['width'] = img.width
            else:
                embed['width'] = 600
            img.close
            embed['height'] = "auto"
            embed['onclick'] = "window.open(\"" + my_embed_path_relative + "\")"
            embed['src'] = my_embed_path_relative

    #
    # dealing with "emoticon"
    #
    my_emoticons = soup.findAll('img',class_=re.compile("emoticon"))     # atlassian-check_mark, or
    print(str(len(my_emoticons)) + " emoticons.")
    for emoticon in my_emoticons:
        request_emoticons = requests.get(emoticon['src'], auth=(arg_username, arg_api_token))
        my_emoticon_title = emoticon['src'].rsplit('/',1)[-1]     # just filename
        if arg_sphinx_compatible == True:
            my_emoticon_path = '../' + my_vars['emoticons_dir'] + my_emoticon_title
        else:
            my_emoticon_path = my_vars['emoticons_dir'] + my_emoticon_title
        if my_emoticon_title not in my_emoticons_list:
            my_emoticons_list.append(my_emoticon_title)
            print("Getting emoticon: " + my_emoticon_title)
            file_path = os.path.join(my_outdirs[1],my_emoticon_title)
            open(file_path, 'wb').write(request_emoticons.content)
        emoticon['src'] = my_emoticon_path

    my_body_export_view = get_body_export_view(arg_site,arg_page_id,arg_username,arg_api_token).json()
    page_url = str(my_body_export_view['_links']['base']) + str(my_body_export_view['_links']['webui'])
    if arg_sphinx_compatible == True:
        styles_dir_relative = str("../" + my_vars['styles_dir'])
    else:
        styles_dir_relative = my_vars['styles_dir']
    my_header = """<html>
<head>
<title>""" + arg_title + """</title>
<link rel="stylesheet" href=\"""" + styles_dir_relative + """confluence.css" type="text/css" />
<meta name="generator" content="confluenceExportHTML" />
<META http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="ConfluencePageLabels" content=\"""" + str(arg_page_labels) + """\">
<meta name="ConfluencePageID" content=\"""" + str(arg_page_id) + """\">
<meta name="ConfluencePageParent" content=\"""" + str(arg_page_parent) + """\">
</head>
<body>
<h2>""" + arg_title + """</h2>
<p>Original URL: <a href=\"""" + page_url + """\"> """+arg_title+"""</a><hr>"""

    myFooter = """</body>
</html>"""
    #
    # At the end of the page, put a link to all attachments.
    #
    if arg_sphinx_compatible == True:
        attach_dir = "../" + my_vars['attach_dir']
    else:
        attach_dir = my_vars['attach_dir']
    if len(my_attachments) > 0:
        my_pre_footer = "<h2>Attachments</h2><ol>"
        for attachment in my_attachments:
            my_pre_footer += ("""<li><a href=\"""" + os.path.join(attach_dir,attachment) + """\"> """ + attachment + """</a></li>""")
        my_pre_footer +=  "</ol></br>"
    #
    # Putting HTML together
    #
    pretty_html = soup.prettify()
    html_file = open(html_file_path, 'w')
    html_file.write(my_header)
    html_file.write(pretty_html)
    if len(my_attachments) > 0:
        html_file.write(my_pre_footer)
    html_file.write(myFooter)
    html_file.close()
    print("Exported HTML file " + html_file_path)
    #
    # convert html to rst
    #
    rst_file_name = str(arg_title) + '.rst'
    rst_file_path = os.path.join(my_outdir_content,rst_file_name)
    try:
        output_rst = pypandoc.convert_file(str(html_file_path), 'rst', format='html',extra_args=['--standalone','--wrap=none','--list-tables'])
    except:
        print("There was an issue generating an RST file from the page.")
    else:
        ##
        ## RST Header with Page Metadata
        ##
        rst_page_header = """.. tags:: """ + str(arg_page_labels) + """

.. meta::
    :confluencePageId: """ + str(arg_page_id) + """
    :confluencePageLabels: """ + str(arg_page_labels) + """
    :confluencePageParent: """ + str(arg_page_parent) + """

"""
        rst_file = open(rst_file_path, 'w')
        rst_file.write(rst_page_header)            # assing .. tags:: to rst file for future reference
        rst_file.write(output_rst)
        rst_file.close()
        print("Exported RST file: " + rst_file_path)
