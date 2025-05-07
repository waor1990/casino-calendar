from dash import Dash
from app_components.layout import create_layout
from app_components.callbacks import register_callbacks

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Casino Event Calendar"

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = create_layout(app)
register_callbacks(app)

server = app.server

# Run the Dash app
if __name__ == '__main__':
    app.run(debug=True)
