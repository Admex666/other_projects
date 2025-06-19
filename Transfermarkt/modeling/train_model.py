def train_and_evaluate_model(merged_df):
    from sklearn.model_selection import train_test_split, cross_validate, KFold
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score

    df = merged_df.copy()
    df['mv_std_rel'] = df['mv_std'] / df['mv_1yr_ago']
    df['mv_since_peak'] = (df['age_']+1) - df['mv_peak_age']
    df['pos_first'] = df['pos_'].str.split(',').str[0]
    df.dropna(subset=['marketValue','mv_pct_change_1yr'], inplace=True)

    target = 'mv_pct_change_1yr'
    X = df[['mv_std_rel', 'age_', 'Playing Time_MP', 'mv_since_peak', 'league_', 'pos_first', 'nation_']]
    y = df[target]

    numeric_features = ['mv_std_rel', 'age_', 'Playing Time_MP', 'mv_since_peak']
    categorical_features = ['league_', 'pos_first', 'nation_']

    numeric_transformer = Pipeline([('scaler', StandardScaler())])
    categorical_transformer = Pipeline([('onehot', OneHotEncoder(handle_unknown='ignore'))])
    preprocessor = ColumnTransformer([
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    pipe = Pipeline([('prep', preprocessor), ('model', model)])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    print(f"Test MAE: {mean_absolute_error(y_test, y_pred):.4f}")
    print(f"Test R²: {r2_score(y_test, y_pred):.4f}")
    return pipe.named_steps['model'], pipe.named_steps['prep'], (X_test, y_test)
