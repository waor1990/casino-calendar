def register_callbacks(app):
    import dash
    from dash import html, dcc, Input, Output, State, MATCH, ALL, ctx, no_update
    import pandas as pd
    from pytz import timezone
    from datetime import datetime, timedelta
    from .plotting import generate_weekly_view, get_color, generate_day_view_html
    from .utils import get_dynamic_sizes, PDT
    from .data import load_event_data
    from .layout import sticky_header
    
    
    PDT = timezone('America/Los_Angeles')
    df = load_event_data()
    
    app.clientside_callback(
    '''
    function(n_intervals) {
        return window.innerWidth;
    }
    ''',
    Output('screen-width', 'data'),
    Input('initial-trigger', 'n_intervals'), 
    State('screen-width', 'data')
)
    
    @app.callback(
        # print(f"Triggered by: {ctx.triggered}"),
        Output('sticky-header', 'children'),
        Input('screen-width', 'data')
    )
    
    def render_sticky_header(screen_width):
        return sticky_header(screen_width)

    @app.callback(
        Output('week-offset', 'data'),
        Output('prev-button', 'disabled'),
        Output('next-button', 'disabled'),
        Output('next-button', 'title'),
        Input('prev-button', 'n_clicks'),
        Input('next-button', 'n_clicks'),
        State('week-offset', 'data')
    )

    def update_week_offset(prev_clicks, next_clicks, current_offset):
        desired_offset = next_clicks - prev_clicks
        
        #Limit going back no more than 6 weeks
        desired_offset = max(-6, desired_offset)
            
        #Limit forward navigation if next 4 weeks are empty
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1 ) % 7)
        start_sunday = current_sunday + timedelta(weeks=desired_offset)
        rolling_weeks = [start_sunday + timedelta(weeks=i) for i in range(4)]
        
        #Get the furthest week in the next 4-week window
        final_week_start = rolling_weeks[-1]
        final_week_end = final_week_start + timedelta(days=6)
        
        #Only allow forward if the last (furthest) week has events
        has_final_week_events = not df[
            (df['EndDate'] > final_week_start) & 
            (df['StartDate'] < final_week_end)
        ].empty
        
        #Don't allow forward if not future events
        if not has_final_week_events and desired_offset > current_offset:
            desired_offset = current_offset
            
        #Disable determination if no events moving forward
        prev_disabled = desired_offset <= -6
        next_disabled = not has_final_week_events
        
        #Dynamic tooltip text for forward navigation
        next_title = "No upcoming events" if next_disabled else "Upcoming 4 Weeks"
        
        return desired_offset, prev_disabled, next_disabled, next_title

    @app.callback(
        Output('rolling-weeks', 'children'),
        Input('week-offset', 'data'),
        Input('initial-trigger', 'n_intervals'),
        State('screen-width', 'data'),
        prevent_initial_call=True
    )

    def render_weeks(week_offset, _, screen_width):
        if week_offset is None or not isinstance(week_offset, int):
            week_offset = 0

        # Recalculate weeks and figures based on the current week offset
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        start_sunday = current_sunday + timedelta(weeks=week_offset)
        rolling_weeks = [start_sunday + timedelta(weeks=i) for i in range(4)]

        font_sizes, padding_sizes = get_dynamic_sizes(screen_width)
        weekly_blocks = []

        for i, start_date in enumerate(rolling_weeks):
            fig, overflow_df = generate_weekly_view(start_date, df, screen_width)
            
            week_key = f"week-{start_date.strftime('%Y%m%d')}"
            end_date = start_date + timedelta(days=6)
            
            toggle_id = {'type': 'toggle-week', 'index': i}
            content_id = {'type': 'week-content', 'index': i}
            
            overflow_width = '80%' if screen_width < 480 else '60%' if screen_width < 768 else '40%'
            
            overflow_content = html.Div(
                id={'type': 'overflow-box', 'index': i},
                className='overflow-box',
                children=[
                    html.Strong("Ongoing Events This Week:", style={
                        'color': '#6A5ACD',
                        'textWeight': 'bold', 
                        'fontSize': font_sizes['overflow'], 
                        'display': 'block', 
                        'marginBottom': '8px'
                    }),
                    html.Ul([
                        html.Li(
                            f"{row['EventName']} ({row['Casino']}) - {row['StartDate'].strftime('%b %d')} to {row['EndDate'].strftime('%b %d')}", 
                            style={'color': '#00008B', 'fontSize': font_sizes['overflow']}
                        )
                        for _, row in overflow_df.iterrows()
                    ])
                ],
                style={
                    'backgroundColor': '#f5f3fa',  # Overflow-box background
                    'padding': '12px 20px',
                    'border': '2px solid #ccc',
                    'borderRadius': '4px',
                    'margin': '0 auto 10px auto',
                    'width': overflow_width,
                    'textAlign': 'left',
                }
            )
            
            weekly_blocks_children = [
                dcc.Store(id={'type': 'week-toggle', 'index': i}, data=False),
                dcc.Store(id={'type': 'toggle-date', 'index': i}, data=start_date.strftime('%Y-%m-%d')),
                dcc.Store(id={'type': 'overflow-date', 'index': i}, data=start_date.strftime('%Y-%m-%d')),
                html.H3(
                    f"▶ Events the Week of {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
                    id=toggle_id,
                    className='week-header',
                    n_clicks=0,
                    style={
                        'fontSize': font_sizes['legend_title'],
                        'color': '#6A5ACD',
                        'fontWeight': 'bold',
                        'cursor': 'pointer',
                        'textAlign': 'center',
                        'userSelect': 'none',
                        'margin': 0
                    }
                ),
                html.Div(
                    id=content_id,
                    className='week-content',
                    children=[
                        dcc.Graph(
                            id={'type': 'graph', 'index': i},
                            figure=fig,
                            config={'displayModeBar': False},
                            style={'width': '99%'}
                        ),
                        html.Div([
                            # Collapse Toggle
                            html.Button(
                                f"🌀 Show Ongoing Events for {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
                                id={'type': 'overflow-toggle', 'index': i},
                                n_clicks=0,
                                style={
                                    'color': '#00008B',
                                    'fontSize': font_sizes['overflow'],
                                    'padding': '2px 4px',
                                    'textAlign': 'center',
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'justifyContent': 'center'
                                }
                            ),
                            overflow_content
                        ]) if not overflow_df.empty else html.Div()
                    ]
                )
            ]
                
            weekly_blocks.append(
                html.Div(
                    weekly_blocks_children,
                    style={'marginBottom': padding_sizes['section_margin']}
                    )
                )      
        
        # Return a list of figures for the weeks
        return weekly_blocks

    @app.callback(
        Output({'type': 'week-content', 'index': MATCH}, 'className'),
        Output({'type': 'week-toggle', 'index': MATCH}, 'data'),
        Input({'type': 'toggle-week', 'index': MATCH}, 'n_clicks'),
        State({'type': 'week-toggle', 'index': MATCH}, 'data'),
        prevent_initial_call=True
    )

    def toggle_week_content(n_clicks, is_open):
        new_is_open = not is_open
        new_class = 'week-content show' if new_is_open else 'week-content'
        return new_class, new_is_open

    @app.callback(
        Output({'type': 'toggle-week', 'index': MATCH}, 'children'),
        Input({'type': 'week-toggle', 'index': MATCH}, 'data'),
        State({'type': 'toggle-date', 'index': MATCH}, 'data')
    )

    def update_toggle_title(is_open, start_date_str):
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = start_date + timedelta(days=6)
        return (
            f"▼ Events the Week of {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
            if is_open else
            f"▶ Events the Week of {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
        )

    @app.callback(
        Output({'type': 'overflow-box', 'index': MATCH}, 'className'),
        Output({'type': 'overflow-toggle', 'index': MATCH}, 'children'),
        Input({'type': 'overflow-toggle', 'index': MATCH}, 'n_clicks'),
        State({'type': 'overflow-date', 'index': MATCH}, 'data'),
        prevent_initial_call=True
    )

    def toggle_overflow(n_clicks, start_date_str):
        # print(f"[toggle_overflow] Clicks: {n_clicks}, Date: {start_date_str}")
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = start_date + timedelta(days=6)
        is_open = n_clicks % 2 == 1

        box_class = 'overflow-box show' if is_open else 'overflow-box'

        button_text = (
            f"🌀 Hide Ongoing Events for {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
            if is_open else 
            f"🌀 Show Ongoing Events for {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
        )

        return box_class, button_text

    @app.callback(
        Output('event-modal', 'style'),
        Output('event-modal', 'className'),
        Output('event-modal-body', 'children'),
        Output('close-timer', 'n_intervals'),
        Output({'type': 'graph', 'index': ALL}, 'clickData'),
        Output('day-modal', 'style'),
        Output('day-modal', 'className'),
        Output('day-modal-body', 'children'),
        Input({'type': 'graph', 'index': ALL}, 'clickData'),
        Input("close-modal", "n_clicks"),
        Input("close-timer", "n_intervals"),
        Input("close-day-modal", "n_clicks"),
        State('week-offset', 'data'),
        prevent_initial_call=True
    )

    def show_event_modal(clicks, close_clicks, timer_tick, close_day_clicks, current_offset):
        ctx = dash.callback_context

        #Make sure clicks is a list
        if not clicks or not isinstance(clicks, list):
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, [], no_update, no_update, no_update
        
        if ctx.triggered_id == "close-timer":
            return no_update, '', '', 0, [None]*len(clicks), {'display': 'none'}, '', ''

        if ctx.triggered_id == "close-modal":
            return no_update, 'modal closing', no_update, 1, [None]*len(clicks), no_update, no_update, no_update
        
        if ctx.triggered_id == "close-day-modal":
            return no_update, no_update, no_update, no_update, no_update, {'display': 'none'}, 'modal closing', ''
        
        #Check for valid clickData    
        for click in clicks:
            if click and 'points' in click and click['points']:
                data = click['points'][0].get('customdata', [None])[0]
                if not data:
                    continue
                
                if data.get("type")  == "day_click":
                    day_index = data.get("day_index")
                    today = datetime.now(PDT)
                    current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
                    start_sunday = current_sunday + timedelta(weeks=current_offset or 0)
                    clicked_day = start_sunday + timedelta(days=day_index)
                    
                    day_view = generate_day_view_html(df, clicked_day, get_color)
                    
                    return no_update, no_update, no_update, no_update, [None]*len(clicks), {'display': 'flex'}, 'modal show', day_view
                
                rows = []
                for label in ["EventName", "Casino", "Location", "StartDate", "EndDate", "Offer"]:
                    if label in data:
                        display_label = {
                            "EventName": "Event",
                            "StartDate": "Event Starts",
                            "EndDate": "Event Ends"
                        }.get(label, label)

                        value = data[label]

                        if label in ["StartDate", "EndDate"]:
                            try:
                                value = pd.to_datetime(value).strftime("%b %d, %Y @ %I:%M %p")
                            except Exception:
                                pass

                        rows.append(html.Div([
                            html.Strong(f"{display_label}: ", style={'color': '#6A5ACD'}),
                            html.Span(value)
                        ], style={'marginBottom': '6px'}))
                return {}, 'modal show', rows, 0, [None]*len(clicks), {'display': 'none'}, '', ''
        #If nothing is valid was clicked
        return no_update, no_update, no_update, no_update, [None]*len(clicks), no_update, no_update, no_update



