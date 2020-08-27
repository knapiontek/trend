dashboard = {'margin': '20px'}

panel = {
    'height': '900px',
    'borderStyle': 'solid',
    'borderWidth': 'thin',
    'overflowX': 'hidden',
    'overflowY': 'auto',
    'padding': '2px'
}


def symbol_table(left_align):
    return dict(
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'left',
            } for c in left_align
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
            'border': '1px solid white'
        },
        style_cell={'padding': '6px'},
        style_data={'border': '1px solid white'},
        style_filter={'border': '1px solid white'}
    )


data_graph = {'width': '100%', 'height': '100%'}
