from Pipeline import Pipeline


class Solo(Pipeline):
    # detect and remove solo quries
    # these can easily be handled on their own
    # as only 1 device is accessing the network at that moment
    def __init__(self, window, debug=False):
        self.DEBUG = debug
        self.window = window

    def detect_solo(self, df_list):
        if self.DEBUG:
            print(df_list)
        new_df = df_list[df_list['ip.src'].ne(df_list['ip.src'].shift())]
        new_df['index_col'] = new_df.index
        new_df['diff'] = new_df['index_col'].diff()
        if self.DEBUG:
            print(new_df)
        new_df = new_df[new_df['diff'] > self.window]
        solo_ips = new_df['ip.src'].unique()
        return solo_ips

    def handle_solo(self, solo):
        if len(solo) > 0 and self.DEBUG:
            print("IPs that must trigger a cache miss: " + str(solo))

    def run_single(self, df_list):
        fil = df_list.loc[:, ['ip.src']]
        solo = self.detect_solo(fil)
        self.handle_solo(solo)
        return solo

    def run(self, scopes):
        solo = [self.run_single(scope.as_df()) for scope in scopes]
        solo = [item for sublist in solo for item in sublist]
        return solo
