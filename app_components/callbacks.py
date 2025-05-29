def register_callbacks(app):
    import dash
    from dash import Input, Output, State, ctx, html, dcc, no_update
    from datetime import datetime, timedelta
    from pytz import timezone
    import pandas as pd
    from .data import load_event_data
    from .plotting import generate_weekly_view, get_color, generate_day_view_html
    from .layout import sticky_header

    PDT = timezone('America/Los_Angeles')
    df = load_event_data()
    
       
    #Screen detection JS (for height + width)
    app.clientside_callback(
        '''
        function(n_intervals) {
            const width = window.innerWidth;
            const height = window.innerHeight;
            
            const header = document.getElementById("app-header");
            const headerHeight = header ? header.offsetHeight : 100;
            
            const usable = Math.max(height - headerHeight - 20, 300);
            return [width, usable];
        }
        ''',
        Output('screen-width', 'data'),
        Output('usable-height', 'data'),
        Input('initial-trigger', 'n_intervals'),
    )
    
    #Sticky header with responsive legend
    @app.callback(
        Output('sticky-header', 'children'),
        Input('screen-width', 'data'),
        Input('week-offset', 'data')
    )
    
    def render_sticky_header(screen_width, week_offset):
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        week_start = current_sunday + timedelta(weeks=week_offset)
        week_label = f"Events for the Week of {week_start.strftime('%B %d')} - {(week_start + timedelta(days=6)).strftime('%B %d, %Y')}"
        
        return sticky_header(week_label)

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
        delta = (next_clicks or 0) - (prev_clicks or 0)
        desired_offset = current_offset + delta
        #Limit going back no more than 6 weeks
        desired_offset = max(-6, desired_offset)
        #Limit forward navigation if next 4 weeks are empty
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        start_sunday = current_sunday + timedelta(weeks=desired_offset)
        
        next_week_offset = desired_offset + 1
        next_week_start = current_sunday + timedelta(weeks=next_week_offset)
        next_week_end = next_week_start + timedelta(days=6)
        
        has_next_week_events = not df[
            (df['EndDate'] > next_week_start) &
            (df['StartDate'] < next_week_end)
        ].empty
        
        if not has_next_week_events and desired_offset > current_offset:
            desired_offset = current_offset
            
        prev_disabled = desired_offset <= -6
        next_disabled = not has_next_week_events
        
        #Dynamic tooltip text for forward navigation
        next_title = "No Upcoming events" if next_disabled else "Upcoming Week"
        
        return desired_offset, prev_disabled, next_disabled, next_title

    @app.callback(
        Output('week-chart-container', 'children'),
        Output('overflow-date', 'data'),
        Input('usable-height', 'data'),
        Input('week-offset', 'data'),
        Input('screen-width', 'data'),
        prevent_initial_call=True
    )
    
    def render_single_week_chart(usable_height, week_offset, screen_width):
        today = datetime.now(PDT)
        current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        week_start = current_sunday + timedelta(weeks=week_offset)
        
        fig, overflow_df = generate_weekly_view(week_start, df)
        
        end_date = week_start + timedelta(days=6)
        
        #Overflow content toggle & box
        if not overflow_df.empty:            
            overflow_toggle = html.Button(
                f"🌀 Show Ongoing Events for {week_start.strftime('%b %d')} - {end_date.strftime('%b %d')}",
                id='overflow-toggle',
                n_clicks=0,
                className='overflow-toggle',
            )
            
            overflow_box = html.Div(
                id='overflow-box',
                className='overflow-box-expand',
                children=[
                    html.Strong("Ongoing Events This Week:", style={
                        'color': '#6A5ACD',
                        'display': 'block',
                        'marginBottom': '8px'
                    }),
                    html.Ul([
                        html.Li(
                            f"{row['EventName']} ({row['Casino']}) - {row['StartDate'].strftime('%b %d')} to {row['EndDate'].strftime('%b %d')}",
                            style={'color': '#00008B'}
                        )
                        for _, row in overflow_df.iterrows()
                    ])
                ]
            )
        else:
            overflow_toggle = html.Div()
            overflow_box = html.Div()
            
        #Shared scrollable container for graph + overflow
        chart = html.Div(
            children=[
                dcc.Graph(
                    id='weekly-graph',
                    figure=fig,
                    config={'displayModeBar': False},
                    style={'width': '100%', 'height': 'auto'}
                ),
                overflow_toggle,
                overflow_box
            ],
            className='slide-in week-chart-scroll',
            style={'height': f'{usable_height}px'},
            key=week_offset
        )
        
        return chart, week_start.strftime('%Y-%m-%d')

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

        box_class = 'overflow-box-expand show' if is_open else 'overflow-box-expand'

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
        Input("day-event-catcher", "clickData"),
        Input("close-modal", "n_clicks"),
        Input("close-timer", "n_intervals"),
        Input("close-day-modal", "n_clicks"),
        State('week-offset', 'data'),
        State('screen-width', 'data'),
        prevent_initial_call=True
    )
    def show_event_modal(weekly_click, day_click, close_clicks, timer_tick, close_day_clicks, week_offset, screen_width):
        ctx = dash.callback_context
        click_reset = None

        if ctx.triggered_id == "close-timer":
            return no_update, '', '', 0, click_reset, {'display': 'none'}, '', ''

        if ctx.triggered_id == "close-modal":
            return no_update, 'modal closing', no_update, 1, click_reset, no_update, no_update, no_update
        
        if ctx.triggered_id == "close-day-modal":
            return no_update, no_update, no_update, no_update, click_reset, {'display': 'none'}, 'modal closing', ''
        
        click_data = None 
        if ctx.triggered_id == "weekly-graph":
            click_data = weekly_click
        elif ctx.triggered_id == "day-event-catcher":
            click_data = day_click
            
        if not click_data or 'points' not in click_data or not click_data['points']:
            return no_update, no_update, no_update, no_update, click_reset, no_update, no_update, no_update
        
        data = click_data['points'][0].get('customdata', [None])[0]
        if not data:
            return no_update, no_update, no_update, no_update, click_reset, no_update, no_update, no_update
        
        #Handle day modal clicks
        if data.get("type") == "day_click":
            day_index = data.get("day_index")
            if day_index is None:
                return no_update, no_update, no_update, no_update, click_reset, no_update, no_update, no_update
            
            today = datetime.now(PDT)
            current_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
            week_start = current_sunday + timedelta(weeks=week_offset)
            clicked_date = week_start + timedelta(days=day_index)
            
            content = generate_day_view_html(df, clicked_date, get_color, screen_width)
            
            return no_update, no_update, no_update, no_update, click_reset, {}, 'modal show', content
        
        #Normal event click
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

                rows.append(
                    html.Div([
                        html.Strong(f"{display_label}: ", style={'color': '#6A5ACD'}),
                        html.Span(value)
                    ], className='event-label')
                )
                
        return {}, 'modal show', rows, 0, None, {'display': 'none'}, '', ''