import io
import os
import sqlite3 as sl
import numpy as np
import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for, send_file
from datetime import datetime
import pytz
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import re

pd.set_option('display.max_columns', None)

file_path = '/Users/moatb/Desktop/Projects/Japan webapp/data/japan_saved_080424.json'
df0 = pd.read_json(file_path)

file_path = '/Users/moatb/Desktop/Projects/Japan webapp/data/additional_080424.json'
to_add = pd.read_json(file_path)

df = pd.concat([df0, to_add], ignore_index=True)

# Define a function to remove non-ASCII characters
def remove_unicode(text):
    if isinstance(text, str):
        # Remove all non-ASCII characters
        return re.sub(r'[^\x00-\x7F]', '', text)
    return text
# Apply the function to all elements in the DataFrame
df_clean = df.applymap(remove_unicode)

# Drop 'info' column
df_clean.drop(columns=['info'], inplace=True)
# Create latitude/longitude columns based on 'gps'
df_clean = df_clean.join(pd.json_normalize(df_clean['gps']))
# Rename the new columns
df_clean.rename(columns={'lat': 'latitude', 'lng': 'longitude'}, inplace=True)
# Convert 'type' column to lowercase
df_clean['type'] = df_clean['type'].str.lower()

def extract_city(plusCode):
    # Split the string by commas
    parts = plusCode.split(', ')
    # Ensure there are at least two commas to have a city part
    if len(parts) > 2:
        # The city is the second to last element
        return parts[-2]
    elif len(parts) <= 2:
        return re.search(r'\+[^ ]+ (.+)$', parts[0]).group(1)
    return None
# Apply the function to the DataFrame
df_clean['city'] = df_clean['plusCode'].apply(extract_city)

def categorize_type(type_str):
    if any(keyword in type_str for keyword in ['dessert', 'pastry', 'sweets', 'confectionery',
                                               'cafeteria', 'bakery', 'cafe', 'tea house',
                                               'traditional teahouse', 'chocolate shop',
                                               'coffee shop', 'souvenir store']):
        return 'Dessert'
    elif type_str == 'shop':
        return 'Dessert'
    elif any(keyword in type_str for keyword in ['restaurant', 'food court', 'stand bar']):
        return 'Food'
    elif any(keyword in type_str for keyword in ['used clothing', 'vintage clothing', 'thrift store', 'racecourse']):
        return 'Thrifting'
    elif any(keyword in type_str for keyword in ['mall', 'clothing store', 'video game store', 'business park',
                                                'discount store']):
        return 'Shopping'
    elif any(keyword in type_str for keyword in ['garden', 'government office', 'tourist attraction',
                                                'observation deck', 'museum', 'tenant ownership']):
        return 'Tourist Attraction'
    elif any(keyword in type_str for keyword in ['salon']):
        return 'Beauty'
df_clean['category'] = df_clean['type'].apply(categorize_type)


# Function to apply K-Means clustering
def apply_kmeans(df, n_clusters=3):
    coords = df[['latitude', 'longitude']].values
    coords = StandardScaler().fit_transform(coords)  # Standardize data

    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(coords)

    # Use .loc to avoid SettingWithCopyWarning
    df.loc[:, 'cluster'] = kmeans.labels_

    return df


# Apply K-Means to each city
results = []
for city in df_clean['city'].unique():
    city_df = df_clean[df_clean['city'] == city].copy()  # Make a copy to avoid SettingWithCopyWarning
    if city == 'Tokyo':
        n_clusters = 7
    elif city == 'Kyoto':
        n_clusters = 3
    elif city == 'Osaka':
        n_clusters = 3
    clustered_df = apply_kmeans(city_df, n_clusters=n_clusters)
    results.append(clustered_df)

# Combine results into a single DataFrame
final_df = pd.concat(results, ignore_index=True)

final_df['city_cluster'] = final_df['city'] + final_df['cluster'].astype(str)

# print(final_df.head())