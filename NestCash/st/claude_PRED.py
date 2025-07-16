import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Time Series Models
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
import pmdarima as auto_arima

# Machine Learning Models
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression, Ridge

# Deep Learning
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

# Anomaly Detection
from scipy import stats

class FinancialPredictiveAnalyzer:
    def __init__(self, data_path=None, df=None):
        """
        Inicializálja az elemzőt CSV fájlból vagy DataFrame-ből
        """
        if df is not None:
            self.df = df.copy()
        elif data_path:
            self.df = pd.read_csv(data_path)
        else:
            raise ValueError("Adjon meg data_path-t vagy df-t")
        
        self.preprocessed_data = None
        self.user_profiles = {}
        self.models = {}
        self.scalers = {}
        
    def preprocess_data(self):
        """
        Adatok előfeldolgozása és tisztítása
        """
        print("Adatok előfeldolgozása...")
        
        # Dátum konverzió
        self.df['datum'] = pd.to_datetime(self.df['datum'])
        
        # Negatív összegek abszolút értéke kiadásokhoz
        self.df['abszolut_osszeg'] = abs(self.df['osszeg'])
        
        # Kiadás/bevétel kategorizálás
        self.df['is_expense'] = self.df['osszeg'] < 0
        self.df['is_income'] = self.df['osszeg'] > 0
        
        # Időalapú változók
        self.df['year'] = self.df['datum'].dt.year
        self.df['month'] = self.df['datum'].dt.month
        self.df['day_of_week'] = self.df['datum'].dt.dayofweek
        self.df['week_of_year'] = self.df['datum'].dt.isocalendar().week
        
        # Kategória kódolás
        self.le_category = LabelEncoder()
        self.df['kategoria_encoded'] = self.le_category.fit_transform(self.df['kategoria'])
        
        self.preprocessed_data = self.df
        print(f"Feldolgozott adatok: {len(self.df)} tranzakció")
        
    def create_user_time_series(self, user_id):
        """
        Felhasználó-specifikus idősor létrehozása
        """
        user_data = self.df[self.df['user_id'] == user_id].copy()
        
        # Havi aggregáció
        monthly_data = user_data.groupby(['year', 'month']).agg({
            'osszeg': 'sum',
            'abszolut_osszeg': 'sum',
            'is_expense': 'sum',
            'kategoria': 'count'
        }).reset_index()
        
        # Dátum index létrehozása
        monthly_data['date'] = pd.to_datetime(monthly_data[['year', 'month']].assign(day=1))
        monthly_data = monthly_data.set_index('date').sort_index()
        
        # Kiadások külön
        expenses_data = user_data[user_data['is_expense']].groupby(['year', 'month']).agg({
            'abszolut_osszeg': 'sum'
        }).reset_index()
        expenses_data['date'] = pd.to_datetime(expenses_data[['year', 'month']].assign(day=1))
        expenses_data = expenses_data.set_index('date').sort_index()
        
        return monthly_data, expenses_data
    
    def arima_forecast(self, user_id, periods=3):
        """
        ARIMA modell havi kiadások előrejelzésére
        """
        print(f"ARIMA előrejelzés felhasználó {user_id}-hez...")
        
        monthly_data, expenses_data = self.create_user_time_series(user_id)
        
        if len(expenses_data) < 6:
            print(f"Túl kevés adat a felhasználóhoz: {user_id}")
            return None
        
        # Idősor előkészítése
        ts = expenses_data['abszolut_osszeg'].fillna(method='ffill')
        
        try:
            # Auto ARIMA paraméter keresés
            model = auto_arima.auto_arima(ts, 
                                        start_p=0, start_q=0,
                                        max_p=3, max_q=3,
                                        seasonal=True, m=12,
                                        stepwise=True,
                                        suppress_warnings=True,
                                        error_action='ignore')
            
            # Előrejelzés
            forecast, conf_int = model.predict(n_periods=periods, return_conf_int=True)
            
            # Eredmények tárolása
            forecast_dates = pd.date_range(start=ts.index[-1] + pd.DateOffset(months=1), 
                                         periods=periods, freq='MS')
            
            results = {
                'model': model,
                'forecast': forecast,
                'confidence_interval': conf_int,
                'dates': forecast_dates,
                'historical_data': ts
            }
            
            self.models[f'arima_{user_id}'] = results
            return results
            
        except Exception as e:
            print(f"ARIMA hiba felhasználó {user_id}-nél: {e}")
            return None
    
    def prepare_lstm_data(self, data, lookback=3):
        """
        LSTM adatok előkészítése
        """
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data.values.reshape(-1, 1))
        
        X, y = [], []
        for i in range(lookback, len(scaled_data)):
            X.append(scaled_data[i-lookback:i, 0])
            y.append(scaled_data[i, 0])
        
        return np.array(X), np.array(y), scaler
    
    def lstm_forecast(self, user_id, periods=3, lookback=3):
        """
        LSTM neural network komplex mintázatokhoz
        """
        print(f"LSTM előrejelzés felhasználó {user_id}-hez...")
        
        monthly_data, expenses_data = self.create_user_time_series(user_id)
        
        if len(expenses_data) < lookback + 3:
            print(f"Túl kevés adat LSTM-hez: {user_id}")
            return None
        
        ts = expenses_data['abszolut_osszeg'].fillna(method='ffill')
        
        try:
            # Adatok előkészítése
            X, y, scaler = self.prepare_lstm_data(ts, lookback)
            
            if len(X) < 3:
                print(f"Túl kevés training adat LSTM-hez: {user_id}")
                return None
            
            # Train/test split
            train_size = max(1, int(len(X) * 0.8))
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Reshape LSTM-hez
            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
            
            # LSTM modell
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(lookback, 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
            
            # Training
            early_stop = EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)
            model.fit(X_train, y_train, epochs=50, batch_size=1, verbose=0, callbacks=[early_stop])
            
            # Előrejelzés
            last_sequence = X[-1].reshape(1, lookback, 1)
            predictions = []
            
            for _ in range(periods):
                pred = model.predict(last_sequence, verbose=0)
                predictions.append(pred[0, 0])
                
                # Új sequence frissítése
                new_sequence = np.append(last_sequence[0, 1:, 0], pred[0, 0])
                last_sequence = new_sequence.reshape(1, lookback, 1)
            
            # Inverz transzformáció
            predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
            
            # Eredmények
            forecast_dates = pd.date_range(start=ts.index[-1] + pd.DateOffset(months=1), 
                                         periods=periods, freq='MS')
            
            results = {
                'model': model,
                'scaler': scaler,
                'forecast': predictions,
                'dates': forecast_dates,
                'historical_data': ts
            }
            
            self.models[f'lstm_{user_id}'] = results
            return results
            
        except Exception as e:
            print(f"LSTM hiba felhasználó {user_id}-nél: {e}")
            return None
    
    def prepare_category_features(self, user_id):
        """
        Kategória-alapú előrejelzéshez feature-ök előkészítése
        """
        user_data = self.df[self.df['user_id'] == user_id].copy()
        
        # Kategóriánkénti havi összesítés
        monthly_category = user_data.groupby(['year', 'month', 'kategoria']).agg({
            'abszolut_osszeg': 'sum',
            'osszeg': 'count'
        }).reset_index()
        
        monthly_category.columns = ['year', 'month', 'kategoria', 'total_amount', 'transaction_count']
        
        # Időalapú feature-ök
        monthly_category['date'] = pd.to_datetime(monthly_category[['year', 'month']].assign(day=1))
        monthly_category['month_sin'] = np.sin(2 * np.pi * monthly_category['month'] / 12)
        monthly_category['month_cos'] = np.cos(2 * np.pi * monthly_category['month'] / 12)
        
        # Lag feature-ök (előző havi költés)
        monthly_category = monthly_category.sort_values(['kategoria', 'date'])
        monthly_category['prev_month_amount'] = monthly_category.groupby('kategoria')['total_amount'].shift(1)
        monthly_category['prev_month_count'] = monthly_category.groupby('kategoria')['transaction_count'].shift(1)
        
        # Rolling statistics
        monthly_category['rolling_mean_3m'] = monthly_category.groupby('kategoria')['total_amount'].rolling(3, min_periods=1).mean().reset_index(0, drop=True)
        monthly_category['rolling_std_3m'] = monthly_category.groupby('kategoria')['total_amount'].rolling(3, min_periods=1).std().reset_index(0, drop=True)
        
        return monthly_category.fillna(0)
    
    def random_forest_category_prediction(self, user_id):
        """
        Random Forest kategória-költések predikciójára
        """
        print(f"Random Forest kategória előrejelzés felhasználó {user_id}-hez...")
        
        category_data = self.prepare_category_features(user_id)
        
        if len(category_data) < 10:
            print(f"Túl kevés kategória adat: {user_id}")
            return None
        
        # Feature és target változók
        feature_cols = ['month', 'month_sin', 'month_cos', 'prev_month_amount', 
                       'prev_month_count', 'rolling_mean_3m', 'rolling_std_3m']
        
        # Kategória encoding
        le_cat = LabelEncoder()
        category_data['kategoria_encoded'] = le_cat.fit_transform(category_data['kategoria'])
        feature_cols.append('kategoria_encoded')
        
        X = category_data[feature_cols].fillna(0)
        y = category_data['total_amount']
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Random Forest modell
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        rf_model.fit(X_train, y_train)
        
        # Előrejelzés tesztre
        y_pred = rf_model.predict(X_test)
        
        # Metrikák
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"Random Forest metrikák - MAE: {mae:.2f}, MSE: {mse:.2f}, R²: {r2:.3f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        results = {
            'model': rf_model,
            'label_encoder': le_cat,
            'feature_importance': feature_importance,
            'metrics': {'mae': mae, 'mse': mse, 'r2': r2},
            'test_predictions': y_pred,
            'test_actual': y_test
        }
        
        self.models[f'rf_category_{user_id}'] = results
        return results
    
    def isolation_forest_anomaly_detection(self, user_id):
        """
        Isolation Forest szokatlan tranzakciókhoz
        """
        print(f"Isolation Forest anomália detektálás felhasználó {user_id}-hez...")
        
        user_data = self.df[self.df['user_id'] == user_id].copy()
        
        if len(user_data) < 20:
            print(f"Túl kevés adat anomália detektáláshoz: {user_id}")
            return None
        
        # Feature-ök anomália detektáláshoz
        features = ['abszolut_osszeg', 'month', 'day_of_week', 'kategoria_encoded']
        
        # Numerikus feature-ök normalizálása
        scaler = StandardScaler()
        X = scaler.fit_transform(user_data[features])
        
        # Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = iso_forest.fit_predict(X)
        
        # Anomália score-ok
        anomaly_scores = iso_forest.decision_function(X)
        
        # Eredmények hozzáadása
        user_data['anomaly'] = anomaly_labels == -1
        user_data['anomaly_score'] = anomaly_scores
        
        # Anomáliák összefoglalása
        anomalies = user_data[user_data['anomaly']].copy()
        
        results = {
            'model': iso_forest,
            'scaler': scaler,
            'anomalies': anomalies,
            'anomaly_count': len(anomalies),
            'anomaly_percentage': len(anomalies) / len(user_data) * 100
        }
        
        self.models[f'isolation_forest_{user_id}'] = results
        return results
    
    def zscore_outlier_detection(self, user_id, threshold=2.5):
        """
        Z-score alapú outlier detection
        """
        print(f"Z-score outlier detektálás felhasználó {user_id}-hez...")
        
        user_data = self.df[self.df['user_id'] == user_id].copy()
        
        # Z-score számítás kategóriánként
        user_data['amount_zscore'] = user_data.groupby('kategoria')['abszolut_osszeg'].transform(
            lambda x: np.abs(stats.zscore(x))
        )
        
        # Outlier-ek azonosítása
        outliers = user_data[user_data['amount_zscore'] > threshold].copy()
        
        results = {
            'outliers': outliers,
            'threshold': threshold,
            'outlier_count': len(outliers),
            'outlier_percentage': len(outliers) / len(user_data) * 100
        }
        
        self.models[f'zscore_{user_id}'] = results
        return results
    
    def comprehensive_user_analysis(self, user_id):
        """
        Komplex felhasználói elemzés minden modellel
        """
        print(f"\n=== Komplex elemzés felhasználó {user_id}-hez ===")
        
        results = {}
        
        # Idősor előrejelzések
        results['arima'] = self.arima_forecast(user_id)
        results['lstm'] = self.lstm_forecast(user_id)
        
        # Kategória előrejelzés
        results['random_forest'] = self.random_forest_category_prediction(user_id)
        
        # Anomália detektálás
        results['isolation_forest'] = self.isolation_forest_anomaly_detection(user_id)
        results['zscore'] = self.zscore_outlier_detection(user_id)
        
        return results
    
    def visualize_results(self, user_id, results):
        """
        Eredmények vizualizálása
        """
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle(f'Pénzügyi Prediktív Elemzés - Felhasználó {user_id}', fontsize=16)
        
        # ARIMA előrejelzés
        if results['arima']:
            ax = axes[0, 0]
            arima_res = results['arima']
            ax.plot(arima_res['historical_data'].index, arima_res['historical_data'].values, 
                   label='Történeti adatok', color='blue')
            ax.plot(arima_res['dates'], arima_res['forecast'], 
                   label='ARIMA előrejelzés', color='red', marker='o')
            ax.fill_between(arima_res['dates'], 
                           arima_res['confidence_interval'][:, 0],
                           arima_res['confidence_interval'][:, 1], 
                           alpha=0.3, color='red')
            ax.set_title('ARIMA Idősor Előrejelzés')
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
        
        # LSTM előrejelzés
        if results['lstm']:
            ax = axes[0, 1]
            lstm_res = results['lstm']
            ax.plot(lstm_res['historical_data'].index, lstm_res['historical_data'].values, 
                   label='Történeti adatok', color='blue')
            ax.plot(lstm_res['dates'], lstm_res['forecast'], 
                   label='LSTM előrejelzés', color='green', marker='s')
            ax.set_title('LSTM Neural Network Előrejelzés')
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
        
        # Random Forest feature importance
        if results['random_forest']:
            ax = axes[0, 2]
            rf_res = results['random_forest']
            rf_res['feature_importance'].plot(x='feature', y='importance', kind='bar', ax=ax)
            ax.set_title('Random Forest Feature Importance')
            ax.tick_params(axis='x', rotation=45)
        
        # Isolation Forest anomáliák
        if results['isolation_forest']:
            ax = axes[1, 0]
            iso_res = results['isolation_forest']
            user_data = self.df[self.df['user_id'] == user_id]
            
            ax.scatter(user_data['datum'], user_data['abszolut_osszeg'], 
                      c='blue', alpha=0.6, label='Normal tranzakciók')
            if len(iso_res['anomalies']) > 0:
                ax.scatter(iso_res['anomalies']['datum'], iso_res['anomalies']['abszolut_osszeg'], 
                          c='red', s=100, label='Anomáliák')
            ax.set_title('Isolation Forest Anomáliák')
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
        
        # Z-score outlier-ek
        if results['zscore']:
            ax = axes[1, 1]
            zscore_res = results['zscore']
            user_data = self.df[self.df['user_id'] == user_id]
            
            ax.hist(user_data['abszolut_osszeg'], bins=30, alpha=0.7, color='blue', label='Összes tranzakció')
            if len(zscore_res['outliers']) > 0:
                ax.hist(zscore_res['outliers']['abszolut_osszeg'], bins=10, alpha=0.8, color='red', label='Z-score outlier-ek')
            ax.set_title('Z-score Alapú Outlier Detektálás')
            ax.legend()
        
        # Összesített statisztikák
        ax = axes[1, 2]
        stats_data = []
        if results['arima']:
            stats_data.append(['ARIMA', 'Sikeres'])
        if results['lstm']:
            stats_data.append(['LSTM', 'Sikeres'])
        if results['random_forest']:
            stats_data.append(['Random Forest', f"R²: {results['random_forest']['metrics']['r2']:.3f}"])
        if results['isolation_forest']:
            stats_data.append(['Isolation Forest', f"{results['isolation_forest']['anomaly_count']} anomália"])
        if results['zscore']:
            stats_data.append(['Z-score', f"{results['zscore']['outlier_count']} outlier"])
        
        ax.axis('tight')
        ax.axis('off')
        table = ax.table(cellText=stats_data, colLabels=['Modell', 'Eredmény'], 
                        cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        ax.set_title('Modell Összefoglaló')
        
        plt.tight_layout()
        plt.show()
    
    def generate_user_report(self, user_id):
        """
        Részletes felhasználói jelentés generálása
        """
        results = self.comprehensive_user_analysis(user_id)
        
        print(f"\n📊 PÉNZÜGYI PREDIKTÍV ELEMZÉS JELENTÉS")
        print(f"👤 Felhasználó: {user_id}")
        print(f"📅 Elemzés dátuma: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*60)
        
        # Alapstatisztikák
        user_data = self.df[self.df['user_id'] == user_id]
        total_transactions = len(user_data)
        total_expenses = user_data[user_data['is_expense']]['abszolut_osszeg'].sum()
        total_income = user_data[user_data['is_income']]['osszeg'].sum()
        avg_transaction = user_data['abszolut_osszeg'].mean()
        
        print(f"📈 ALAPSTATISZTIKÁK:")
        print(f"   • Összes tranzakció: {total_transactions}")
        print(f"   • Összes kiadás: {total_expenses:,.0f} HUF")
        print(f"   • Összes bevétel: {total_income:,.0f} HUF")
        print(f"   • Átlagos tranzakció: {avg_transaction:,.0f} HUF")
        
        # Előrejelzési eredmények
        print(f"\n🔮 ELŐREJELZÉSI MODELLEK:")
        
        if results['arima']:
            next_month_arima = results['arima']['forecast'][0]
            print(f"   • ARIMA előrejelzés következő hónapra: {next_month_arima:,.0f} HUF")
        
        if results['lstm']:
            next_month_lstm = results['lstm']['forecast'][0]
            print(f"   • LSTM előrejelzés következő hónapra: {next_month_lstm:,.0f} HUF")
        
        if results['random_forest']:
            rf_r2 = results['random_forest']['metrics']['r2']
            print(f"   • Random Forest kategória modell pontossága: {rf_r2:.1%}")
        
        # Anomália detektálás eredményei
        print(f"\n⚠️  ANOMÁLIA DETEKTÁLÁS:")
        
        if results['isolation_forest']:
            anomaly_count = results['isolation_forest']['anomaly_count']
            anomaly_pct = results['isolation_forest']['anomaly_percentage']
            print(f"   • Isolation Forest: {anomaly_count} anomália ({anomaly_pct:.1f}%)")
        
        if results['zscore']:
            outlier_count = results['zscore']['outlier_count']
            outlier_pct = results['zscore']['outlier_percentage']
            print(f"   • Z-score módszer: {outlier_count} outlier ({outlier_pct:.1f}%)")
        
        # Javaslatok
        print(f"\n💡 SZEMÉLYRE SZABOTT JAVASLATOK:")
        
        if results['isolation_forest'] and results['isolation_forest']['anomaly_count'] > 0:
            print(f"   • Figyeljen oda a szokatlan kiadásokra - {results['isolation_forest']['anomaly_count']} anomáliát találtunk")
        
        if results['arima'] and results['lstm']:
            arima_pred = results['arima']['forecast'][0]
            lstm_pred = results['lstm']['forecast'][0]
            avg_pred = (arima_pred + lstm_pred) / 2
            print(f"   • Várható következő havi kiadás: {avg_pred:,.0f} HUF (modellek átlaga)")
        
        # Vizualizáció
        self.visualize_results(user_id, results)
        
        return results

# Használati példa
def main():
    """
    Főprogram
    """
    
    df = pd.read_csv('szintetikus_tranzakciok.csv')
    
    # Elemző inicializálása
    analyzer = FinancialPredictiveAnalyzer(df=df)
    
    # Adatok előfeldolgozása
    analyzer.preprocess_data()
    
    # Egy felhasználó részletes elemzése
    user_id = 39
    report = analyzer.generate_user_report(user_id)
    
    print(f"\nElemzés befejezve! A modellek elmentve az analyzer.models dictionary-ben.")

if __name__ == "__main__":
    main()
