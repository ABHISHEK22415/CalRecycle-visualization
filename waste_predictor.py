import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder


class WastePredictor:
    def load_data(self):
        file_path = './BusinessGroupsForAMaterial.xlsx'
        sheet_name = 'Data-Commercial Business Groups'

        # Load the correct sheet
        data = pd.read_excel(file_path, sheet_name=sheet_name)
        return data


    def encode_jurisdiction(self, data, load=False):
        # Preprocess the data
        if load:
            label_encoder = joblib.load('./label_encoder.pkl')
            data['Jurisdiction(s)'] = label_encoder.fit_transform(data['Jurisdiction(s)'])
        else:
            label_encoder = LabelEncoder()
            data['Jurisdiction(s)'] = label_encoder.fit_transform(data['Jurisdiction(s)'])
            joblib.dump(label_encoder, 'label_encoder.pkl')


    def train_business_type_model(self, business_group, data):
        # Filter data for the first business group
        data_bg1 = data[data['Business Group'] == business_group]

        # Define the target columns
        target_cols = ['Tons Curbside Recycle', 'Tons Curbside Organics', 'Tons Other Diversion']

        # Train a separate model for each target column
        # for target_col in target_cols:

        # Define the feature and target data
        x = data_bg1[['Employee Count', 'Jurisdiction(s)']]
        y = data_bg1[target_cols]

        # Split the data into training and testing sets
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

        # Train the model
        model = LinearRegression()
        model.fit(x_train, y_train)

        # Make predictions on the testing set
        y_pred = model.predict(x_test)

        # Calculate the evaluation metrics
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        return model, {'MAE': mae, 'MSE': mse, 'R2': r2}


    def train_models(self, data, save=False):
        # Extracting unique business groups
        business_groups = data['Business Group'].unique()

        # Initialize a dictionary to store the models and their evaluation metrics
        models = {}
        metrics = {}

        for business_group in business_groups:
            model, m_metrics = self.train_business_type_model(business_group, data)
            # Store the model and its metrics
            models[business_group] = model
            metrics[business_group] = m_metrics

            if save:
                # Save the model
                joblib.dump(model, f'./models/{business_group}.pkl')


    def predict(self, data):
        # Load the model
        model = joblib.load(f'./models/{data["Business Group"][0]}.pkl')

        self.encode_jurisdiction(data, load=True)

        # Make the prediction
        predictions = model.predict(data[['Employee Count', 'Jurisdiction(s)']])
        return {
            'Tons Curbside Recycle': predictions[0][0],
            'Tons Curbside Organics': predictions[0][1],
            'Tons Other Diversion': predictions[0][2],
            # 'Total Tons': predictions[0][0] + predictions[0][1] + predictions[0][2]
        }


if __name__ == '__main__':
    waste_predictor = WastePredictor()
    train = False
    if train:
        data = waste_predictor.load_data()
        waste_predictor.encode_jurisdiction(data, load=False)
        waste_predictor.train_models(data, save=True)
    else:
        data = pd.DataFrame({
            'Business Group': ['Services - Professional, Technical, & Financial'],
            'Jurisdiction(s)': ['Los Angeles (Countywide)'],
            'Employee Count': [10]
        })
        print(waste_predictor.predict(data))