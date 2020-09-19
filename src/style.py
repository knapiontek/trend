def symbol_table(**kwargs):
    return dict(
        style_cell_conditional=[
            {
                'if': {'column_id': k},
                'textAlign': v,
            } for k, v in kwargs.items()
        ],
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(229, 236, 246)'
            }
        ],
        style_header={
            'backgroundColor': 'rgb(200, 212, 227)',
            'fontWeight': 'bold',
            'border': '1px solid white',
            'paddingLeft': '3px',
            'textAlign': 'left'
        },
        style_cell={'padding': '4px'},
        style_data={'border': '1px solid white'},
        style_filter={'border': '1px solid white'}
    )
