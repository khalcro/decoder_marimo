# /// script
# dependencies = [
#     "altair==6.2.2",
#     "marimo",
#     "polars==1.43.2",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="full")


@app.cell
def _():
    from enum import Enum, auto
    from pathlib import Path
    import polars as pl
    import altair as alt

    return Enum, Path, alt, pl


@app.cell
def _():
    # TODO
    ## upload csv from ST decoder  DONE
    ## parse existing dataset for locales
    ## plot multiple locales against each other DONE
    ## handle rounding value DONE
    ## remove all callbacks and use marimo native reactivity!!!!!! DONE
    return


@app.cell
def _(Enum, Path, mo, pl):
    # setup the inputs

    _can_form_dict = {
        'current_assets': 'Current Assets',
        'capital_assets': 'Capital Assets',
        'liabilities': 'Liabilities',
        'revenues_total': 'Revenues(total)',
        'other': 'Other',
        'government_transfers': 'Government Transfers',
        'government_transfers_related_to_capital': 'Government Transfers related to Capital',
        'interest_charges': 'Interest Charges',
        'net_book_tca': 'Net Book TCA',
        'total_cost_of_tca': 'Total Cost of TCA',
    }

    _us_form_dict = {
        'current_assets': 'Current Assets',
        'capital_assets': 'Capital Assets',
        'deferred_outflows': 'Deferred Outflows',
        'liabilities': 'Liabilities',
        'deferred_inflows': 'Deferred Inflows',
        'total_revenues': 'Total Revenues',
        'operating_grants_and_contributions': 'Operating Grants and Contributions',
        'capital_grants_and_contributions': 'Capital Grants and Contributions',
        'interest_charges': 'Interest Charges',
        'net_book_tca': 'Net Book TCA',
        'govt_assets_not_depreciated': 'Govt assets not depreciated',
        'govt_assets_being_depreciated': 'Govt assets being depreciated',
        'govt_other_assets': 'Govt other assets',
        'bus_assests_not_depreciated': 'Bus assets not depreciated',
        'bus_assets_being_depreciated': 'Bus assets being depreciated',
        'bus_other_assets': 'Bus other assets',
    }

    def _make_form_markdown(country: str):
        if country == 'can':
            _dict = _can_form_dict
        else:
            _dict = _us_form_dict
        return mo.md(
        '**Enter values as per the instructions in the [Strong Towns Decoder](https://www.strongtowns.org/decoder-resources)**' 
        +
        '\n\n{country}'
        +
        '\n\n{city}'
        +
        '\n\n{year}'
        +
        ''.join([f'\n\n{{{key}}}' for key in _dict])
        +
        '\n\n{rounding}'
    )

    class Entry:
        """
        this class performs all calculations for the input data
        """
        descriptive_cols = {
            'city': pl.String,
            'year': pl.Int16,
            'country': pl.String,
        }
        # all inputs are integer.. i would hope
        input_cols = {key: pl.Int32 for key in list(dict.fromkeys([k for k in _us_form_dict] + [k for k in _can_form_dict]))}
        calculated_cols = {key: pl.Int32 for key in ['total_assets', 'total_liabilities', 'net_position', 'total_revenues', 'total_government_transfers', 'net_financial_position']}
        ratio_cols = {key: pl.Float32 for key in ['financial_assets-to-liabilities', 'assets-to-liabilities', 'net_debt-to-total-revenues', 'interest-to-total_revenues', 'net_book-to-cost_of_tca', 'govt_transfers-to-total_revenues']}
        metadata_cols = {'rounding': pl.String, '_rounding': pl.Float32}

        schema = descriptive_cols | input_cols | calculated_cols | ratio_cols | metadata_cols

        class Country(Enum):
            CANADA = 1
            US = 2

        data = {}

        def determine_country(self, country_str: str):
            self.country = getattr(self.Country, country_str.upper())

        def retype_data(self):
            self.data.update({key: int(val) for key, val in self.data.items() if self.schema[key] != pl.String and val is not None})

        def calculate_summaries(self):
            self.data['total_assets'] = self.data['current_assets'] + self.data['capital_assets']

            if self.country is self.Country.CANADA:
                self.data['total_liabilities'] = self.data['liabilities']
                self.data['net_position'] = self.data['total_assets'] - self.data['total_liabilities']
                self.data['total_revenues'] = self.data['revenues_total'] + self.data['other']
                self.data['total_government_transfers'] = self.data['government_transfers'] + self.data['government_transfers_related_to_capital']

            if self.country is self.Country.US:
                self.data['total_liabilities'] = self.data['liabilities'] + self.data['deferred_inflows']
                self.data['net_position'] = self.data['total_assets'] + self.data['deferred_outflows'] - self.data['total_liabilities']
                self.data['total_government_transfers'] = self.data['operating_grants_and_contributions'] + self.data['capital_grants_and_contributions']
                self.data['total_cost_of_tca'] = self.data['govt_assets_not_depreciated'] + self.data['govt_assets_being_depreciated'] + self.data['govt_other_assets'] + self.data['bus_assests_not_depreciated'] + self.data['bus_assets_being_depreciated'] + self.data['bus_other_assets']

        def calculate_indicators(self):
            self.data['net_financial_position'] = self.data['current_assets'] - self.data['total_liabilities']
            def safe_divide(n, d):  # catch divide by zero
                return n/d if d else 0
            self.data['financial_assets-to-liabilities'] = safe_divide(self.data['current_assets'], self.data['total_liabilities'])
            if self.country is self.Country.CANADA:
                self.data['assets-to-liabilities'] = safe_divide(self.data['total_assets'], self.data['total_liabilities'])
            if self.country is self.Country.US:
                self.data['assets-to-liabilities'] = safe_divide(self.data['total_assets'] + self.data['deferred_outflows'], self.data['total_liabilities'])
            self.data['net_debt-to-total-revenues'] = safe_divide(self.data['net_financial_position'], self.data['total_revenues']) if self.data['net_financial_position'] < 0 else 0
            self.data['interest-to-total_revenues'] = safe_divide(self.data['interest_charges'], self.data['total_revenues'])
            self.data['net_book-to-cost_of_tca'] = safe_divide(self.data['net_book_tca'], self.data['total_cost_of_tca'])
            self.data['govt_transfers-to-total_revenues'] = safe_divide(self.data['total_government_transfers'], self.data['total_revenues'])

        def calculate_rounding_scale(self):
            _rounding_dict = {
                'dollars': 1/1000,
                'thousands': 1,
                'millions': 1000,
            }
            self.data.update({'_rounding': _rounding_dict[self.data['rounding']]})

        def convert_to_dataframe(self, data={}):
            """
            take the input data dictionary and convert it to a polars dataframe
            :param data: dict, can be empty to return empty dataframe
            """
            if len(data) == 0:
                return pl.DataFrame(schema=self.schema)
            self.data = data
            self.determine_country(data['country'].upper())
            self.retype_data()
            self.calculate_summaries()
            self.calculate_indicators()
            self.calculate_rounding_scale()
            self.data.update({key: None for key in self.schema if key not in self.data})
            return pl.DataFrame(data=self.data, schema=self.schema, strict=False)


    def manual_entry_callback(manual_form_list):
        """
        converts the data from the manual entry form to a dataframe
        """
        if len(manual_form_list) > 0:
            new_df = pl.concat((Entry().convert_to_dataframe(data=manual_form)) for manual_form in manual_form_list)
        else:
            new_df = Entry().convert_to_dataframe(data={})
        return new_df

    def upload_callback(filebrowser_form):
        filebrowser = filebrowser_form.value
        if filebrowser is None:
            return Entry().convert_to_dataframe(data={})
        sources = filebrowser['_input_section']
        if len(sources) > 0:
            source_dfs = [read_csv(s) for s in sources]
        return pl.concat(source_dfs, how='vertical')

    def read_csv(file_obj):
        """
        reads the input csv, and feeds into the existing framework
        """
        # common work
        path = Path(file_obj.name)
        df = pl.read_csv(path, has_header=False)  # we can just read the csv, it's pretty small
        city = path.stem
        rounding = df[2, 6]

        # check if second col contains "Canada" i.e. "N/A for Canada" -- this is maybe the best indicator I could find
        if df.select(pl.col('column_2').str.contains('Canada').any()).item():
            country = 'Canada'
            subset_df = (
                df[[4,6,7,10,14,15,17,18,20,21,22], 3:] # only the input data -- matches the keys in _can_form_dict
                 .with_columns(pl.col(pl.Utf8).str.strip_chars())  # trim all whitespace in strings
                 .with_columns(pl.col(pl.Utf8).str.replace_all(',', ''))  # remove commas (thousands sep)
                 .with_columns(pl.all().cast(pl.Int64))  # cast to int
            )
            keys = ['country', 'city', 'year'] + [*_can_form_dict.keys()] + ['rounding']

        else:
             country = 'US'
             subset_df = (
                 df[[3,5,6,8,9,10,13,14,15,17,18,19,20,21,22,23,24], 4:] # only the input data -- matches the keys in _us_form_dict
                  .with_columns(pl.col(pl.Utf8).str.strip_chars())  # trim all whitespace in strings
                  .with_columns(pl.col(pl.Utf8).str.replace_all(',', ''))  # remove commas (thousands sep)
                  .with_columns(pl.all().cast(pl.Int64))  # cast to int
             )
             keys = ['country', 'city', 'year'] + [*_us_form_dict.keys()] + ['rounding']

        series = []
        for cc in subset_df.iter_columns():
            if not cc.is_null().any():  # check if we're missing any data
                vals = [country, city, *cc.to_list(), rounding]
                series.append(Entry().convert_to_dataframe(data=dict(zip(keys, vals))))
            else:
                series.append(Entry().convert_to_dataframe({}))
        return pl.concat(series, how='vertical')

    can_form_getter, can_form_setter = mo.state([])
    us_form_getter, us_form_setter = mo.state([])

    def _form_validator(manual_form):
        if all(isinstance(val, int) for key, val in manual_form.items() if key not in ['country', 'rounding']):
            return
        else:
            return "Fill out all entries before submitting"

    can_form = _make_form_markdown('can').batch(
        country=mo.ui.text(label='Country', value='Canada', disabled=True),
        city=mo.ui.text(label='City'),
        year=mo.ui.text(label='Year'),
        **{key: mo.ui.text(label=value) for key, value in _can_form_dict.items()},
        rounding=mo.ui.radio(options=['dollars', 'thousands', 'millions'], value='dollars', label='Report Rounding', inline=True)
    ).form(show_clear_button=True, bordered=False, clear_on_submit=True, validate=_form_validator)

    us_form = _make_form_markdown('us').batch(
        country=mo.ui.text(label='Country', value='US', disabled=True),
        city=mo.ui.text(label='City'),
        year=mo.ui.text(label='Year'),
        **{key: mo.ui.text(label=value) for key, value in _us_form_dict.items()},
        rounding=mo.ui.radio(options=['dollars', 'thousands', 'millions'], value='dollars', label='Report Rounding', inline=True)
    ).form(show_clear_button=True, bordered=False, clear_on_submit=True, validate=_form_validator)

    upload_form = mo.md(
        """
        Upload a spreadsheet downloaded from the strongtowns finance decoder worksheet in csv form
        {_input_section}
        """).batch(
        _input_section=mo.ui.file(filetypes=['.csv'], multiple=True, kind='area', label='Select an exported csv. Filename will be used as the city/locale name.')).form(bordered=False)

    input_section = mo.accordion({'Input new': mo.ui.tabs({'Canada': can_form, 'US': us_form}),
                                 'Upload ST csv file': upload_form})



    _repo_data_path = mo.notebook_location() / 'public' / 'decoded.parquet'
    if _repo_data_path.exists():
        existing_df_lazy = pl.scan_parquet(_repo_data_path)
    else:
        existing_df_lazy = pl.LazyFrame(schema=Entry().convert_to_dataframe(data={}).schema)
    return (
        can_form,
        can_form_getter,
        can_form_setter,
        input_section,
        manual_entry_callback,
        upload_callback,
        upload_form,
        us_form,
        us_form_getter,
        us_form_setter,
    )


@app.cell
def _(can_form, can_form_setter, us_form, us_form_setter):
    can_form_setter(lambda v: v + [can_form.value] if can_form.value is not None else v)
    us_form_setter(lambda v: v + [us_form.value] if us_form.value is not None else v)
    return


@app.cell
def _(input_section):
    input_section
    return


@app.cell
def _(
    can_form_getter,
    manual_entry_callback,
    pl,
    upload_callback,
    upload_form,
    us_form_getter,
):
    can_form_df = manual_entry_callback(can_form_getter())
    us_form_df = manual_entry_callback(us_form_getter())
    upload_df = upload_callback(upload_form)
    input_df = pl.concat((can_form_df, us_form_df, upload_df))
    return (input_df,)


@app.cell
def _(input_df, pl):
    # because we smrt all input data is int32 and we can round that to the thousands easily
    rounded_df = input_df.with_columns(pl.col(pl.Int32) * pl.col('_rounding'))
    return (rounded_df,)


@app.cell
def _(alt, mo, pl, rounded_df):
    mo.stop(len(rounded_df) == 0, mo.md('**upload files to see graphs**'))
    # select by city using the legend
    _chart_selector = alt.selection_point(fields=['city'], bind='legend')
    # bring the selected values to the front
    _selected_on_top = alt.when(_chart_selector).then(alt.value(1)).otherwise(alt.value(0))
    # make a legend scale so that entries don't get filtered out from the legend when clicked on in the legend (weird deadlock possible if this scale doesn't exist)
    _legend_scale = alt.Scale(domain=rounded_df['city'].unique().to_list())
    # make a year scale
    _year_scale = (rounded_df['year'].min() - 0.5, rounded_df['year'].max() + 0.5)


    _titles = [
        "Net Financial Position (In Thousands of Dollars)",
        "Financial Assets-to-Total Liabilities",
        "Total Assets-To-Total Liabilities",
        "Net Debt-to-Total Revenues",
        "Interest-to-Total Revenues",
        "Net Book Value-to-Cost of Tangible Capital Assets",
        "Government Transfers-to-Total Revenues"
    ]
    _y_data_keys = rounded_df.select(('net_financial_position', pl.col(pl.Float32))).drop('_rounding').columns
    _y_titles = [
        "Cumulative Surplus/Deficit (Thousands of Dollars)",
        "Ratio (Financial Assets:Total Liabilities)",
        "Ratio (Total Assets:Total Liabilities)",
        "Ratio (Net Debt:Total Revenues)",
        "Percentage (Revenue Spent on Interest)",
        "Percentage (Current Value of Assets to Original Cost)",
        "Percentage (City's Income from State or Fed. Aid)",
    ]


    charts = [
        alt.Chart(rounded_df, title=_chart_title).mark_line(point=True).encode(
            alt.X('year')
                .axis(tickMinStep=1, grid=False)  # tick marks every 1, no grid
                .scale(domain=_year_scale, nice=True)  # use nice=True to pad the axis
                .title('Year'),
            alt.Y(_y_data)
                .axis(format=('%' if 'Percentage' in _y_title else ',.3r'))
                .scale(zero=False, nice=True)
                .title(_y_title),
            alt.Color('city', scale=_legend_scale),
            order=_selected_on_top,
        )
        .add_params(
            _chart_selector if i ==0 else alt.param()  # only create the selector once!
        )
        .transform_filter(
            _chart_selector  # filter out non-selected data
        )
        for i, (_chart_title, _y_data, _y_title) in enumerate(zip(_titles, _y_data_keys, _y_titles))
    ]
    return (charts,)


@app.cell
def _(alt, charts, mo):
    cc = mo.ui.altair_chart(alt.hconcat(*(alt.vconcat(*charts[0:4]), alt.vconcat(*charts[4:7]))))
    return (cc,)


@app.cell
def _(cc):
    cc
    return


@app.cell
def _(cc):
    cc.value
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
