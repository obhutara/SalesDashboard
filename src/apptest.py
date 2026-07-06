# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


from dash import Dash, dcc, html
import plotly.express as px
import pandas as pd
from datetime import datetime as dt
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash.exceptions import PreventUpdate
import io
import xlsxwriter
import base64
#import dash_auth

app = Dash(__name__)
server = app.server
app.title = "Rishi Minerals Sales"

customers = pd.read_excel('customers.xlsx')
df = pd.DataFrame(customers, columns=['Particulars','Product','total_sale_value','total_gst','gross_Total',
                                                         'quantity','mean_price','total_number_bills','agent','Date'])
df = df.loc[df["mean_price"] <= 30000]
df["agent"] = df["agent"].astype(str)
df['Date'] = pd.to_datetime(df['Date'])
df["Particulars"] = df["Particulars"].astype(str)
df["Product"] = df["Product"].astype(str)

download_button = html.Button("Download Excel file", id="btn", style={"marginTop": 20})
download_component = dcc.Download(id="download_excel")

#VALID_USERNAME_PASSWORD_PAIRS = {
#    'omkar': 'omkar',
#    'sandesh': 'sandesh'
#}

fig = px.scatter(df, x="mean_price", y="quantity",
                 size="total_sale_value", color="Product",
                 hover_name="Particulars", hover_data=['agent'],
                 log_x=False, log_y=True, size_max=70)
fig.update_layout(xaxis_range=[0, 10000], yaxis_range=[0, 1000])

app.layout = html.Div([
    #dash_auth.BasicAuth(
    #    app,
    #    VALID_USERNAME_PASSWORD_PAIRS
    #),
    dcc.Graph(
        id='sales',
        figure=fig
    ),
    html.H1("Select Date Range in months and Agents Checkbox"),
    dcc.DatePickerRange(
        id='date-picker-range',
        min_date_allowed=dt(2022, 1, 1),
        max_date_allowed=dt(2026, 6, 30),
        start_date=dt(2026, 6, 1),
        end_date=dt(2026, 6, 30)
    ),
    html.Div(children=[
        html.Label('Checkboxes'),
        dcc.Checklist(
            id='agents',
            options=[
                {'label': 'Sunil Rathi', 'value': 'Sunil Rathi'},
                {'label': 'Shresth Maheshwari', 'value': 'Shresth Maheshwari'},
                {'label': 'Abhijit Maloo', 'value': 'Abhijit Maloo'},
                {'label': 'Direct', 'value': 'Direct'},
                {'label': 'Vishnu Kankani', 'value': 'Vishnu Kankani'}
    ],
    value=['Sunil Rathi', 'Shresth Maheshwari', 'Abhijit Maloo', 'Direct', 'Vishnu Kankani']
                    )
    ]),
    html.Div(id='table-container', children=[
        dash_table.DataTable(
            id='table',
            columns=[],
            data=[],
            filter_action='native',
            sort_action='native',
            sort_mode='multi',
            page_action='native',
            page_current=0,
            page_size=20,
            style_cell={'textAlign': 'left'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        ),

        html.Div(id='product-summary')
    ]),
    html.Div(
        [html.H2("Filtered Data Download", style={"marginBottom": 20}), download_component, download_button, ]
    )
], style={'padding': 10, 'flex': 1})


@app.callback(
    Output('sales', 'figure'),
    Output('table', 'columns'),
    Output('table', 'data'),
    Output('product-summary', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('agents', 'value')
)
def update_chart(start_date, end_date, agents):

    if not start_date or not end_date:
        raise PreventUpdate

    if agents is None:
        agents = []

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)

    filtered_df = df[
        (df['Date'] >= start_date) &
        (df['Date'] < end_date) &
        (df['agent'].isin(agents))
    ].copy()

    grouped_df = filtered_df.groupby(
        ['Particulars', 'Product'],
        as_index=False
    ).agg({
        'quantity': 'sum',
        'total_sale_value': 'sum',
        'total_number_bills': 'sum',
        'agent': 'first'
    })

    grouped_df['mean_price'] = 0.0
    mask = grouped_df['quantity'] != 0
    grouped_df.loc[mask, 'mean_price'] = (
        grouped_df.loc[mask, 'total_sale_value'] /
        grouped_df.loc[mask, 'quantity']
    )

    grouped_df = grouped_df[
        [
            'Particulars',
            'Product',
            'quantity',
            'mean_price',
            'total_number_bills',
            'total_sale_value',
            'agent'
        ]
    ]

    grouped_df = grouped_df.sort_values('quantity', ascending=False)

    table_columns = [{'name': i, 'id': i} for i in grouped_df.columns]
    table_data = grouped_df.round(2).to_dict('records')

    product_summary_df = grouped_df.groupby(
        'Product',
        as_index=False
    ).agg({
        'quantity': 'sum',
        'total_sale_value': 'sum'
    })

    product_summary_df['mean_price'] = 0.0
    product_mask = product_summary_df['quantity'] != 0
    product_summary_df.loc[product_mask, 'mean_price'] = (
        product_summary_df.loc[product_mask, 'total_sale_value'] /
        product_summary_df.loc[product_mask, 'quantity']
    )

    total_quantity_all = product_summary_df['quantity'].sum()
    total_sale_value_all = product_summary_df['total_sale_value'].sum()

    mean_price_all = (
        total_sale_value_all / total_quantity_all
        if total_quantity_all != 0 else 0
    )

    footer_rows = []

    for _, row in product_summary_df.iterrows():
        footer_rows.append(
            html.Tr([
                html.Td(f'Total {row["Product"]}'),
                html.Td(f'{row["quantity"]:,.2f}'),
                html.Td(f'{row["mean_price"]:,.2f}')
            ])
        )

    footer_rows.append(
        html.Tr([
            html.Td('Total All Products'),
            html.Td(f'{total_quantity_all:,.2f}'),
            html.Td(f'{mean_price_all:,.2f}')
        ], style={'fontWeight': 'bold'})
    )

    footer_table = html.Div([
        html.H3('Product-wise Total Quantity and Mean Price'),

        html.Table([
            html.Thead(
                html.Tr([
                    html.Th('Product'),
                    html.Th('Total Quantity'),
                    html.Th('Mean Price')
                ])
            ),
            html.Tbody(footer_rows)
        ], style={
            'marginTop': '10px',
            'borderCollapse': 'collapse'
        })
    ])

    # For log scale, remove zero or negative quantities from the chart only.
    # Table and totals will still show the full grouped data.
    chart_df = grouped_df[grouped_df['quantity'] > 0].copy()

    if chart_df.empty:
        fig = px.scatter(title='No data for selected filters')
    else:
        # Plotly marker size cannot be negative.
        # Use absolute value for bubble size, but keep actual total_sale_value in hover.
        chart_df['bubble_size'] = chart_df['total_sale_value'].abs()
        chart_df.loc[chart_df['bubble_size'] == 0, 'bubble_size'] = 1

        fig = px.scatter(
            chart_df,
            x='mean_price',
            y='quantity',
            size='bubble_size',
            color='Product',
            hover_name='Particulars',
            hover_data={
                'quantity': ':.2f',
                'mean_price': ':.2f',
                'total_number_bills': True,
                'total_sale_value': ':.2f',
                'agent': True,
                'bubble_size': False
            },
            log_x=False,
            log_y=True,
            size_max=70
        )

    fig.update_layout(
        margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
        hovermode='closest',
        uirevision='sales-dashboard'
    )

    fig.update_xaxes(range=[0, 10000])

    # Important: for log_y=True, Plotly expects log10 range.
    # [0, 3] means actual y-axis range 1 to 1000.
    fig.update_yaxes(range=[0, 3])

    return fig, table_columns, table_data, footer_table

#def dataframe_to_excel(df):
#    output = io.BytesIO()
#    writer = pd.ExcelWriter(output, engine='xlsxwriter')
#   df.to_excel(writer, sheet_name='Sheet1', index=False)
#    writer.save()
#    xlsx_data = output.getvalue()
#    return base64.b64encode(xlsx_data).decode()

@app.callback(
    Output('download_excel', 'data'),
    Input('btn', 'n_clicks'),
    State('table', 'data'),
    prevent_initial_call=True
)
def download_data(n_clicks, table_data):

    if not n_clicks:
        raise PreventUpdate

    if not table_data:
        raise PreventUpdate

    dff = pd.DataFrame(table_data)

    return dcc.send_data_frame(dff.to_csv, "SalesFiltered.csv", index=False)



if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
