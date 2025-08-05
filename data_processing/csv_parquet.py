import pandas as pd

# Load CSV
df = pd.read_csv('data_processing/etc/books.csv')

# Drop 'isbn10', 'isbn', and 'thumbnail' if they exist
df = df.drop(columns=['isbn10', 'isbn', 'thumbnail'], errors='ignore')

# Rename 'large_thumbnail' to 'thumbnail' if it exists
if 'large_thumbnail' in df.columns:
    df = df.rename(columns={'large_thumbnail': 'thumbnail'})

# Replace 'data/cover-not-found.jpg' with 'cover-not-found.jpg' in 'thumbnail' column
if 'thumbnail' in df.columns:
    df['thumbnail'] = df['thumbnail'].replace('data/cover-not-found.jpg', 'cover-not-found.jpg')

# Ensure 'isbn13' is string
df['isbn13'] = df['isbn13'].astype('string')

# Convert all object columns to StringDtype
object_cols = df.select_dtypes(include=['object']).columns
df[object_cols] = df[object_cols].astype('string')

# Convert count-like columns to nullable integers (Int64 handles NaN safely)
int_cols = ['published_year', 'num_pages', 'ratings_count']
for col in int_cols:
    if col in df.columns:
        df[col] = df[col].astype('Int64')  # Nullable integer type

# Save to Parquet
df.to_parquet('books.parquet', index=False)

# Load back to verify schema is preserved
df_loaded = pd.read_parquet('books.parquet')

# Print dtypes to verify
print(df_loaded.dtypes)
