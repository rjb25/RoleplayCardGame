import json # Yes, we're using this instead of a DB. I know.
import itty3 # Should be installed already, as indicated by requirements.txt, https://itty3.readthedocs.io

dmapp = itty3.App() # Object creation function for itty3

@dmapp.get("/")
def index(request):
    '''Handles the "/" route for DM Assistant

    This will be where the main input and output occurs
    while this is a single-page web application.

    Varous buttons and links on the index page that gets loaded and populated
    by this will invoke other functions of the DM assistant.
    '''
    # Open the HTML file that we'll be using
    # as the main place to render any updates to
    # this single-page web app.
    with open("index.html") as index_file:
        template = index_file.read()

    # Load JSON web_data.json to use from storage local
    # to the file. Needs to be in the same folder as
    # web_app.py.
    with open("web_data.json") as data_file:
        data = json.load(data_file)

    content = ""

    # Make the list that we'll be pushing in later and replacing
    # {{ content }} with.
    for offset, item in enumerate(data.get("updates", [])):
        content += "<li>{}</li>".format(item)

    if not content:
        content = "<li>Nothing to do!</li>"

    # Find and replace "{{content}}" in the HTML with our new update
    template = template.replace("{{ content }}", content)

    # Build and render an HttpResponse object including our content
    # and various boilerplate things like headers
    return dmapp.render(request, template)

@dmapp.post("/update_cmd/")
def append_update_cmd(request):
    '''This just updates a table of commands as entered.

    You can invoke it by adding web links to an HTML page
    that refer to /update_cmd/.
    '''

    # Load JSON web_data.json
    with open("web_data.json") as data_file:
        data = json.load(data_file)

    # Get the new text. "---" is just boilerplate that will be replaced,
    # I guess. Not much documentation on what it means.
    # Make sure that there is a value in your form or whatever that
    # makes the POST that is named "update_cmd" or this will just
    # become "---", which now that I think of it is probably a default value.
    new_update_cmd = request.POST.get("update_cmd", "---").strip()
    
    # Add the new item to the list. 
    # Again, this will just be "---" if no value named "update_cmd" posted.
    data["updates"].append(new_update_cmd)

    # Update the actual file in storage, hence the "w".
    with open("web_data.json", "w") as data_file:
        json.dump(data, data_file, indent=4)

    # For a single-page application like this, we should
    # usually re-route back to the main index page, typically at "/".
    return dmapp.redirect(request, "/")

# This just makes sure that we can still import this as 
# a library or run it standalone.
if __name__ == "__main__":
    dmapp.run()
