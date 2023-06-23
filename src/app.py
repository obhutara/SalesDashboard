# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


from dash import Dash, dcc, html
import plotly.express as px
import pandas as pd
from datetime import datetime as dt
from dash.dependencies import Input, Output, State
from dash import dash_table
import io
import xlsxwriter
import base64
#import dash_auth

app = Dash(__name__)
server = app.server
app.title = "Sales Bubble Chart"

customers = pd.read_excel('customers.xlsx')
df = pd.DataFrame(customers, columns=['Particulars','Product','total_sale_value','total_gst','gross_Total',
                                                         'quantity','mean_price','total_number_bills','agent','Date'])
df = df.loc[df["mean_price"] <= 15000]
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
        max_date_allowed=dt(2023, 6, 30),
        start_date=dt(2023, 6, 1),
        end_date=dt(2023, 6, 30)
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
                {'label': 'Vishnu Kankani', 'value': 'Vishnu Kankani'},
                {'label': 'Sharad Bhutra', 'value': 'Sharad Bhutra'}
    ],
    value=['Sunil Rathi', 'Shresth Maheshwari', 'Abhijit Maloo', 'Direct', 'Vishnu Kankani','Sharad Bhutra']
                    )
    ]),
    html.Div(id='table-container', children=[
        dash_table.DataTable(
            id='table',
            columns=[{'name': i, 'id': i} for i in df.columns],
            data=df.to_dict('records'),
            filter_action='native',
            style_cell={'textAlign': 'left'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            sort_action='native',
            page_action='native',
            page_current=0,
            page_size=20
      )
    ]),
    html.Div(
        [html.H2("Filtered Data Download", style={"marginBottom": 20}), download_component, download_button, ]
    )
], style={'padding': 10, 'flex': 1})


@app.callback(
    Output('sales', 'figure'),
    Output('table-container', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('agents', 'value')
)

def update_chart(start_date, end_date, agents):
    filtered_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date) & (df['agent'].isin(agents))]
    # Group the data by Particulars, Product, and agent
    grouped_df = filtered_df.groupby(['Particulars', 'Product']).agg({
                                                                  'quantity': 'sum',
                                                                  'mean_price': 'mean',
                                                                  'total_number_bills': 'sum',
                                                                  'total_sale_value': 'sum',
                                                                  'agent':'first'
                                                                  }).reset_index()
    # Group the data by Product to calculate the total quantity by product
    grouped_product_df = grouped_df.groupby('Product').agg({'quantity': 'sum'}).reset_index()
    # Calculate the total quantity across all products
    total_quantity_all = grouped_product_df['quantity'].sum()

    # Define the table columns
    table_columns = [{'name': i, 'id': i} for i in grouped_df.columns]

    # Define the table data
    table_data = grouped_df.sort_values('quantity', ascending=False).to_dict('records')

    # Create the table
    table = dash_table.DataTable(
        id='table',
        columns=table_columns,
        data=table_data,
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
    )

    # Create the footer rows
    footer_rows = []
    for product in grouped_product_df['Product']:
        total_quantity = grouped_product_df.loc[grouped_product_df['Product'] == product, 'quantity'].iloc[0]
        footer_row = html.Tr([
            html.Td(f'Total {product}'),
            html.Td(total_quantity)
        ])
        footer_rows.append(footer_row)

    # Add a row for the total across all products
    total_row = html.Tr([
        html.Td('Total All Products'),
        html.Td(total_quantity_all)
    ])
    footer_rows.append(total_row)

    # Wrap the table and footer rows in a div with a title
    footer_title = html.P('Total Quantities', style={'fontWeight': 'bold'})
    footer_div = html.Div([
        footer_title,
        html.Table(footer_rows)
    ])
    # Combine the table and footer rows
    table_with_footer = html.Div([
        table,
        html.Table(footer_rows)
    ])

    fig = px.scatter(grouped_df, x="mean_price", y="quantity",
                     size="total_sale_value", color="Product",
                     hover_name="Particulars",hover_data=['quantity', 'mean_price',
                                                          'total_number_bills','total_sale_value','agent'],
                                                          log_x=False, log_y=True, size_max=70)
    fig.update_layout(xaxis_range=[0, 10000], yaxis_range=[0, 1000])
    fig.update_layout(uirevision='autoscale')
    table_data = grouped_df.sort_values('quantity', ascending=False).to_dict('records')
    table = dash_table.DataTable(
        id='table',
        columns=[{'name': i, 'id': i} for i in grouped_df.columns],
        data=table_data,
        style_cell={'textAlign': 'left'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        sort_action='native',
        page_action='native',
        page_current=0,
        page_size=20
    )
    return fig,table_with_footer

#def dataframe_to_excel(df):
#    output = io.BytesIO()
#    writer = pd.ExcelWriter(output, engine='xlsxwriter')
#   df.to_excel(writer, sheet_name='Sheet1', index=False)
#    writer.save()
#    xlsx_data = output.getvalue()
#    return base64.b64encode(xlsx_data).decode()

@app.callback(
    Output('download_excel', 'data'),
    [Input('btn', 'n_clicks')],
    [State('table', 'data')]
)
#def download_excel(n_clicks, table_data):
#    if n_clicks:
#        df = pd.DataFrame.from_records(table_data)
#        return dict(content=dataframe_to_excel(df), filename='download.xlsx',
#                    type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
def download_data(n_clicks, table_data):
    dff = pd.DataFrame(table_data)
    return dcc.send_data_frame(dff.to_csv, "SalesFiltered.csv")



if __name__ == '__main__':
    app.run_server(debug=True)

