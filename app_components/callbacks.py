def register_callbacks(app):
    import dash
    from dash import html, dcc, Input, Output, State, ctx, no_update
    import pandas as pd
    from pytz import timezone
    from datetime import datetime, timedelta
    from .plotting import generate_weekly_view, get_color, generate_day_view_html
    from .utils import get_dynamic_sizes, PDT
    from .data import load_event_data
    from .layout import sticky_header
    
    
    PDT = timezone('America/Los_Angeles')
    df = load_event_data()
    
    #Detect screen width once
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
    
    #Sticky header with responsive legend
    @app.callback(
        Output('sticky-header', 'children'),
        Input('screen-width', 'data')
    )
    
    def render_sticky_header(screen_width):
        return sticky_header(screen_width)

    #Update week offset on button clicks
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
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
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
        next_title = "No Upcoming events" if next_disabled else "Upcoming Week"
        
        return desired_offset, prev_disabled, next_disabled, next_title

    @app.callback(
        Output('week-chart-container', 'children'),
        Output('overflow-date', 'data'),
        Input('week-offset', 'data'),
        Input('screen-width', 'data'),
        prevent_initial_call=True
    )
    
    def render_single_week_chart(week_offset, screen_width):
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        week_start = current_sunday + timedelta(weeks=week_offset)
        
        fig, overflow_df = generate_weekly_view(week_start, df, screen_width)
        font_sizes, padding_sizes = get_dynamic_sizes(screen_width)
        
        week_title = html.H3(
            f"Events for the Week of {week_start.strftime('%B %d')} - {(week_start + timedelta(days=6)).strftime('%B %d, %Y')}",
            style={
                'position': 'sticky',
                'top': '60px',
                'zIndex': 900,
                'backgroundColor': 'white',
                'padding': f"{padding_sizes.get('xxs', '6px')} 0",
                'textAlign': 'center',
                'fontSize': font_sizes.get('legend_title', '1.2rem'),
                'fontWeight': 'bold',
                'color': '#00008B',
                'boxShadow': '0 1px 2px rgba(0,0,0,0.1)',
                'margin': '0 auto'
            }
        )
        
        #Overflow content toggle & box
        if not overflow_df.empty:
            end_date = week_start + timedelta(days=6)
            
            overflow_toggle = html.Button(
                f"🌀 Show Ongoing Events for {week_start.strftime('%b %d')} - {end_date.strftime('%b %d')}",
                id='overflow-toggle',
                n_clicks=0,
                style={
                    'color': '#00008B',
                    'fontSize': font_sizes['overflow'],
                    'padding': '2px 4px',
                    'textAlign': 'center',
                    'display': 'flex',
                    'justifyContent': 'center',
                    'margin': '10px auto'
                }
            )
            
            overflow_box = html.Div(
                id='overflow-box',
                className='overflow-box',
                children=[
                    html.Strong("Ongoing Events This Week:", style={
                        'color': '#6A5ACD',
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
                    'backgroundColor': '#f5f3fa',
                    'padding': '12px 20px',
                    'border': '2px solid #ccc',
                    'borderRadius': '4px',
                    'width': '60%' if screen_width < 760 else '40%',
                    'margin': '10px auto',
                    'textAlign': 'left',
                }
            )
        else:
            overflow_toggle = html.Div()
            overflow_box = html.Div()
            
        #Shared scrollable container for graph + overflow
        scrollable_content = html.Div([
            dcc.Graph(
                id='weekly-graph',
                figure=fig,
                config={'displayModeBar': False},
                style={'width': '100%', 'height': 'auto'}
            ),
            overflow_toggle,
            overflow_box
        ], style={
            'maxHeight': '600px',
            'overflowY': 'auto',
            'padding': f"0 {padding_sizes.get('small', '12px')}",
            'marginBottom': '0'
        })
        
        return html.Div([week_title, scrollable_content]), week_start.strftime('%Y-%m-%d')

    @app.callback(
        Output('overflow-box', 'className'),
        Output('overflow-toggle', 'children'),
        Input('overflow-toggle', 'n_clicks'),
        State('overflow-date', 'data'),
        prevent_initial_call=True
    )

    def toggle_overflow(n_clicks, start_date_str):
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
        Output('weekly-graph', 'clickData'),
        Output('day-modal', 'style'),
        Output('day-modal', 'className'),
        Output('day-modal-body', 'children'),
        Input('weekly-graph', 'clickData'),
        Input("close-modal", "n_clicks"),
        Input("close-timer", "n_intervals"),
        Input("close-day-modal", "n_clicks"),
        State('week-offset', 'data'),
        State('screen-width', 'data'),
        prevent_initial_call=True
    )
    def show_event_modal(click_data, close_clicks, timer_tick, close_day_clicks, current_offset, screen_width):
        ctx = dash.callback_context
        click_reset = None

        if ctx.triggered_id == "close-timer":
            return no_update, '', '', 0, click_reset, {'display': 'none'}, '', ''

        if ctx.triggered_id == "close-modal":
            return no_update, 'modal closing', no_update, 1, click_reset, no_update, no_update, no_update
        
        if ctx.triggered_id == "close-day-modal":
            return no_update, no_update, no_update, no_update, click_reset, {'display': 'none'}, 'modal closing', ''
        
        if not click_data or 'points' not in click_data or not click_data['points']:
            return no_update, no_update, no_update, no_update, click_reset, no_update, no_update, no_update
        
        data = click_data['points'][0].get('customdata', [None])[0]
        if not data:
            return no_update, no_update, no_update, no_update, click_reset, no_update, no_update, no_update
                          
        if data.get("type")  == "day_click":
            day_index = data.get("day_index")
            today = datetime.now(PDT)
            current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
            week_start = current_sunday + timedelta(weeks=current_offset or 0)
            clicked_day = week_start + timedelta(days=day_index)
            
            day_view = generate_day_view_html(df, clicked_day, get_color, screen_width)    
            return no_update, no_update, no_update, no_update, click_reset, {'display': 'flex'}, 'modal show', day_view
        
        #Regular event click
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
        return {}, 'modal show', rows, 0, click_reset, {'display': 'none'}, '', ''