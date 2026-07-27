# /// script
# dependencies = [
#     "marimo",
#     "polars==1.43.0",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import polars as pl
    from enum import Enum, auto

    return Enum, pl


@app.cell
def _(Enum, mo, pl):
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
        metadata_cols = {'rounding': pl.String}
    
        schema = descriptive_cols | input_cols | calculated_cols | ratio_cols | metadata_cols

        class Country(Enum):
            CANADA = 1
            US = 2

        data = {}
    
        def determine_country(self, country_str: str):
            self.country = getattr(self.Country, country_str.upper())

        def retype_data(self):
            self.data.update({key: int(val) for key, val in self.data.items() if self.schema[key] != pl.String})
    
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

        def convert_to_dataframe(self, data={}):
            if len(data) == 0:
                return pl.DataFrame(schema=self.schema)
            self.data = data
            self.determine_country(data['country'].upper())
            self.retype_data()
            self.calculate_summaries()
            self.calculate_indicators()
            breakpoint()
            self.data.update({key: None for key in self.schema if key not in self.data})
            return pl.DataFrame(data=self.data, schema=self.schema, strict=False)
        
    # setup dataframes with typing
    input_df = Entry().convert_to_dataframe(data={})

    def append_form_input(form):
        new_df = Entry().convert_to_dataframe(data=form)
    
        global input_df
        input_df.vstack(new_df, in_place=True)

    _can_form = _make_form_markdown('can').batch(
        country=mo.ui.text(label='Country', value='Canada', disabled=True),
        city=mo.ui.text(label='City'),
        year=mo.ui.text(label='Year'),
        **{key: mo.ui.text(label=value) for key, value in _can_form_dict.items()},
        rounding=mo.ui.radio(options=['dollars', 'thousands', 'millions'], value='dollars', label='Report Rounding', inline=True)
    ).form(show_clear_button=True, bordered=False, on_change=append_form_input)

    _us_form = _make_form_markdown('us').batch(
        country=mo.ui.text(label='Country', value='US', disabled=True),
        city=mo.ui.text(label='City'),
        year=mo.ui.text(label='Year'),
        **{key: mo.ui.text(label=value) for key, value in _us_form_dict.items()},
        rounding=mo.ui.radio(options=['dollars', 'thousands', 'millions'], value='dollars', label='Report Rounding', inline=True)
    ).form(show_clear_button=True, bordered=False, on_change=append_form_input)

    input_section = mo.accordion({'Input new': mo.ui.tabs({'Canada': _can_form, 'US': _us_form})})



    _repo_data_path = mo.notebook_location() / 'public' / 'decoded.parquet'
    if _repo_data_path.exists():
        existing_df_lazy = pl.scan_parquet(_repo_data_path)
    else:
        existing_df_lazy = pl.LazyFrame(schema=Entry().convert_to_dataframe(data={}).schema)

    return input_df, input_section


@app.cell
def _(input_df):
    print(input_df)
    return


@app.cell
def _(input_section):
    input_section
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
