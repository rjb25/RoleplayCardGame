import json # Yes, we're using this instead of a DB. I know.
import itty3 # Should be installed already, as indicated by requirements.txt, https://itty3.readthedocs.io
import basic # This is how we'll reference the functions of the main game logic
import os # This is to show filenames and shit like that.

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

    content = ''
    battle_state_content = ''
    last_roll_content = ''

    # Make the list that we'll be pushing in later and replacing
    # {{ content }} with.
    for offset, item in enumerate(data.get("updates", [])):
        content += '<li>{}</li>'.format(item)

    if not content:
        content = '<li>Nothing to do!</li>'

    # Find and replace "{{ content }}" in the HTML with our new update
    template = template.replace('{{ content }}', content)

    # Update the Battle State
    battle_state_list = basic.getState()
    LOGGER.info(battle_state_list)

    # Make the list that we'll be pushing in later and replacing
    # {{ battle_state_content }} with.
    for participant in battle_state_list:
        battle_state_content += '<li>{}</li>'.format(participant)

    LOGGER.info(battle_state_content)

    # Find and replace "{{ battle_state_content }}" in the HTML with our new update
    template = template.replace('{{ battle_state_content }}', battle_state_content)

    # Show the last Roll Result

    for offset, item in enumerate(data.get("rolls", [])):
        last_roll_content = '<li>{}</li>'.format(item)

    # Find and replace "{{ last_roll_content }}" in the HTML with our new update
    template = template.replace('{{ last_roll_content }}', last_roll_content)

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
    
    # Now it's time to do something with that data.
    # We'll do 3 operations: 
    #  1. Update the web page.
    #  2. Update the JSON.
    #  3. Parse the command

    # 1. Update the web page.
    # Add the new item to the list in the web page.
    # Again, this will just be "---" if no value named "update_cmd" posted.
    data["updates"].append(new_update_cmd)

    # 2. Update the JSON
    # Update the actual file in storage, hence the "w".
    with open("web_data.json", "w") as data_file:
        json.dump(data, data_file, indent=4)

    # 3. Parse the command text
    # Get the first word
    LOGGER.info("Command List is as follows: " + str(new_update_cmd))
    basic.parse_command(new_update_cmd)

    # For a single-page application like this, we should
    # usually re-route back to the main index page, typically at "/".
    return dmapp.redirect(request, "/")

@dmapp.post("/roll/")
def roll(request):
    '''Roll dice or something

    You can invoke it by adding web links to an HTML page
    that refer to /roll/.

    Inputs expected are the type and number of dice.

    Outputs will be the results, in a list or dict of
    integers.
    '''

    dice_string = request.POST.get("dice_string", "1d20").strip()
    LOGGER.info('dice_string indicating the dice to roll is: ' + str(dice_string))

    # Load JSON web_data.json
    with open("web_data.json") as data_file:
        data = json.load(data_file)

    # Roll the dice
    roll_result = basic.roll(dice_string)
    LOGGER.info('Roll result is: ' + str(roll_result))

    # Update rolls
    data["rolls"].append(roll_result)
    with open("web_data.json", "w") as data_file:
        json.dump(data, data_file, indent=4)

    return dmapp.redirect(request, "/")

# This just makes sure that we can still import this as 
# a library or run it standalone.
if __name__ == "__main__":

    # -------- Logging Setup -------- #
    # We're going to use the logger from
    # the dmapp object, which it has because
    # the itty3 class creates a logger upon
    # instantiation.
    LOGGER = dmapp.get_log()
    LOGGER.setLevel('INFO')
    LOGGER.info(os.path.basename(__file__))
    # -------- End Logging Setup ---- #
    
    basic.setBattleOrder()

    # This runs the app. This won't be run if
    # web_app gets imported.
    dmapp.run(addr="0.0.0.0",
        port=8000,
        debug=None,
        static_url_path=None,
        static_root=None,
    )
