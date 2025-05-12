from dash import html, dcc
from .utils import get_dynamic_sizes
from .data import load_event_data
from .plotting import get_color

def create_layout(app): 
    screen_width = 1024
    font_sizes, padding_sizes = get_dynamic_sizes(screen_width)
    
    return html.Div(
    style={
        'fontFamily': 'Segoe UI, sans-serif',
        'margin': '0 auto',
        'paddingBottom': '40px'
    },
    children=[
        #Sticky-Header container
        html.Div(id='sticky-header', style={
            'position': 'sticky',
            'top': 0,
            'padding': f"{padding_sizes['header_padding']} 0",
            'backgroundColor': 'white',
            'zIndex': 1000,
            'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.25)'
        }),
        
        #Loading spinner and calendar weeks
        dcc.Loading(
            id='calendar-loading',
            type='circle',
            color='#6A5ACD',
            children=html.Div(
                id='rolling-weeks',
                style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'gap': padding_sizes['week_gap'],
                    'marginTop': padding_sizes['section_margin']
            }),
        ),
        
        #State Stores and Timers
        dcc.Store(id='screen-width', data=1024), 
        dcc.Store(id='week-offset', data=0),
        dcc.Interval(id='initial-trigger', interval=1, max_intervals=1),
        dcc.Interval(id='close-timer', interval=600, n_intervals=0, max_intervals=0),
     
        #Modal Popup for event details
        html.Div(id='event-modal', className='modal', children=[
            html.Div(id='event-modal-content', className='modal-content', children=[
                html.Div(id='event-modal-body', style={
                    "maxHeight": "80vh", 
                    "overflow": "scroll",
                    "padding": "10px"
                    }),
                html.Button("Close", id="close-modal", style={
                    'marginTop': '10px',
                    'display': 'block',
                    'marginLeft': 'auto',
                    'marginRight': 'auto',
                    'backgroundColor': '#6A5ACD',
                    'color': 'white',
                    'border': 'none',
                    'padding': '8px 16px',
                    'borderRadius': '6px',
                    'cursor': 'pointer'
                })
            ])
        ]),
        
        #Day-Modal Popup for day's events
        html.Div(id='day-modal', className='modal', children=[
            html.Div(id='day-modal-content', className='modal-content', children=[
                html.Div(id='day-modal-body', style={
                    "maxHeight": "80vh",
                    "overflowY": "scroll",
                    "padding": "10px"
                }),
                html.Button("Close", id="close-day-modal", style={
                    'marginTop': '10px',
                    'display': 'block',
                    'marginLeft': 'auto',
                    'marginRight': 'auto',
                    'backgroundColor': '#6A5ACD',
                    'color': 'white', 
                    'border': 'none',
                    'padding': '8px 16px',
                    'borderRadius': '6px',
                    'cursor': 'pointer'
                })
            ])
        ])
    ]
    )
    
def sticky_header(screen_width):
    font_sizes, padding_sizes = get_dynamic_sizes(screen_width)
    df = load_event_data()

    return html.Div([
        html.H1(
            "🎰 Casino Event Calendar 📅",
            style={
                'textAlign': 'center',
                'margin': '0',
                'fontSize': font_sizes['h1'],
                'marginBottom': '20px',
                'color': 'inherit',
                'padding': f"{padding_sizes['header_padding']} 0",
            }
        ),
        #Navigation & Legend
        html.Div(
            id='header-container',
            children=[
            html.Button(
                "🎲",
                id='prev-button',
                title="Prior 4 Weeks",
                n_clicks=0,
                className='emoji-button',
                style={'fontSize': font_sizes['button'], 'padding': padding_sizes['button_padding']}
            ),
            html.Div([
                html.Legend(
                    "Casino Legend:",
                    style={
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'fontSize': font_sizes['legend_title'],
                        'marginBottom': padding_sizes['legend_gap']
                    }
                ),
                html.Div(
                    create_legend(font_sizes, padding_sizes, df),
                    style={
                        'display': 'flex',
                        'flexWrap': 'wrap',
                        'justifyContent': 'center',
                        'alignItems': 'flex-start',
                        'textAlign': 'left',
                        'gap': f"{int(padding_sizes['legend_gap'].replace('px', '')) // 2}px"
                    }
                )
            ], style={'flex': '1', }),
            html.Button(
                "🎰",
                id='next-button',
                n_clicks=0,
                className='emoji-button',
                style={'fontSize': font_sizes['button'], 'padding': padding_sizes['button_padding']}
            )
        ],
        style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'gap': '10px',
            'paddingBottom': '10px',
        }
        )
    ])

def create_legend(font_sizes, padding_sizes, df):
    df = load_event_data()
    legend_items = []
    for casino, color in get_color().items():
        if casino in df['Casino'].unique():
            legend_items.append(html.Div([
                html.Div(
                    style={
                        'backgroundColor': color["bg"],
                        'width': '20px',
                        'height': '20px',
                        'display': 'inline-block',
                        'marginRight': '6px'
                    }
                ),
                html.Span(
                    f"{casino}",
                    style={
                        'color': color["bg"],
                        'marginRight': '4px',
                        'fontSize': font_sizes['legend']
                    }
                )
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'margin': f"0 {padding_sizes['legend_gap']} {padding_sizes['legend_gap']} 0",
                'flex': '0 1 auto',
            }))
    return legend_items