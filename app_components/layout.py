from dash import html, dcc
import plotly.graph_objs as go
from .data import load_event_data
from .plotting import get_color

def create_layout(app):
    return html.Div(
    className="main-layout",
    children=[
        #Header section only (wrapped for height calc)
        html.Div(
            id="app-header", 
            children=
                #Sticky-Header container
                html.Div(
                    id='sticky-header', 
                    className='sticky-header header-padding',
                )
        ),
        #Scrollable Calendar Body
        html.Div(
            id="calendar-scroll-body",
            className="calendar-scroll-body",
            children=[
                #Main calendar area
                dcc.Loading(
                    id='calendar-loading',
                    type='circle',
                    color='#6A5ACD',
                    children=html.Div(
                        id='week-chart-container',
                        className='week-gap section-margin calendar-content',
                    ),
                ),
                #Optional Dev Preview Section
                html.Div(
                    id="day-preview-toggle",
                    children=html.Button(
                        "Preview Grid Layout",
                        id="preview-grid-button",
                        n_clicks=0,
                        className="emoji-button",
                    ),
                    style={"textAlign": "center", "marginBottom": "20px"}
                ),
                html.Div(
                    id="dev-preview-output",
                    className="calendar-content",
                ),
            ]           
        ),
                        
        #State Stores
        dcc.Store(id='usable-height', data=600),
        dcc.Store(id='screen-width', data=1024),
        dcc.Store(id='week-offset', data=0),
        dcc.Store(id='overflow-date'),
        #Interval Triggers
        dcc.Interval(id='initial-trigger', interval=1, max_intervals=1),
        dcc.Interval(id='close-timer', interval=600, n_intervals=0, max_intervals=0),
        #Invisible catcher for click events
        dcc.Graph(
            id="day-event-catcher", 
            figure=go.Figure(), 
            style={
                "visibility": "hidden",
                "height": "0px",
                "pointerEvents": "none"
            }
        ),
    
        #Event Modal Popup
        html.Div(id='event-modal', className='modal', children=[
            html.Div(id='event-modal-content', className='modal-content', children=[
                html.Div(id='event-modal-body', className="base-padding", style={
                    "maxHeight": "80vh", 
                    "overflow": "auto",
                }),
                html.Button(
                    "Close",
                    id="close-modal",
                    className="modal-close"
                )
            ])
        ]),
        
        #Day Modal Popup
        html.Div(id='day-modal', className='modal', children=[
            html.Div(id='day-modal-content', className='modal-content', children=[
                html.Div(id='day-modal-body', className='base-padding', style={
                    "maxHeight": "80vh",
                    "overflowY": "auto",
                }),
                html.Button("Close", id="close-day-modal", className="modal-close")
            ])
        ])
    ]
)

    
def sticky_header(week_start_label=""):
    df = load_event_data()
    return html.Div([
        html.H1(
            "🎰 Casino Event Calendar 📅",
            className="calendar-title",
        ),
        #Navigation & Legend
        html.Div(
            id='header-container',
            children=[
                html.Button(
                    "🎲",
                    id='prev-button',
                    title="Prior Week",
                    n_clicks=0,
                    className='emoji-button',
                ),
                html.Div([
                    html.Legend(
                        "Casino Legend:",
                        className="legend-title legend-gap",
                    ),
                    html.Div(
                        create_legend(df),
                        className="legend-container"
                    )
                ], style={'flex': '1', }),
                html.Button(
                    "🎰",
                    id='next-button',
                    n_clicks=0,
                    className='emoji-button',
                )
            ],
            style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'gap': '10px',
                'paddingBottom': '10px',
            }
        ),
        #Week Label
        html.Div(
            week_start_label, 
            key=week_start_label,
            className="fade-text calendar-title section-margin week-label",            
        ),
    ]
)

def create_legend(df):
    df = load_event_data()
    legend_items = []
    for casino, color in get_color().items():
        if casino in df['Casino'].unique():
            legend_items.append(html.Div(
                className="legend-item",
                children=[
                    html.Div(
                        className="legend-color-box",
                        style={
                            'backgroundColor': color["bg"],
                        }
                    ),
                    html.Span(
                        f"{casino}",
                        className="legend-text legend-gap",
                        style={
                            'color': color["bg"],
                            'marginRight': '4px'
                        }
                    )
                ])
        )
    return legend_items