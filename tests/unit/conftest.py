import pandas as pd
import pytest

@pytest.fixture
def sample_books():
    """ Reusable DataFrame for testing across all test files

        Basic stats
            simple_categories:
                Fiction - 6 (George Orwell, Stephen King x2, Harper Lee, Bill Bryson)
                Non-Fiction - 2 (Malcolm Gladwell, Bill Bryson)
                Children's Fiction - 3 (J.K. Rowling x2, Roald Dahl)
                Children's Non-Fiction - 1 (National Geographic Kids)

            Authors with multiple books:
                Stephen King - 2 books (The Shining, It)
                J.K. Rowling - 2 books (Sorcerer's Stone, Chamber of Secrets)

            Pages: [80, 120, 180, 200, 250, 300, 341, 350, 400, 1138]
    """

    data = [
        {
            'isbn13': '9780451524935',
            'title': '1984',
            'authors': 'George Orwell',
            'simple_categories': 'Fiction',
            'num_pages': 200,
            'description': 'A dystopian novel about a totalitarian regime that controls every aspect of life through surveillance and propaganda.',
            'joy': 0.1, 'surprise': 0.2, 'anger': 0.4, 'fear': 0.8, 'sadness': 0.7
        },
        {
            'isbn13': '9780439708180',
            'title': "Harry Potter and the Sorcerer's Stone",
            'authors': 'J.K. Rowling',
            'simple_categories': "Children's Fiction",
            'num_pages': 300,
            'description': 'A young wizard discovers his magical heritage on his eleventh birthday and begins his education at Hogwarts School of Witchcraft and Wizardry.',
            'joy': 0.9, 'surprise': 0.7, 'anger': 0.1, 'fear': 0.2, 'sadness': 0.1
        },
        {
            'isbn13': '9780385121675',
            'title': 'The Shining',
            'authors': 'Stephen King',
            'simple_categories': 'Fiction',
            'num_pages': 400,
            'description': 'A horror novel about a writer who becomes winter caretaker at an isolated hotel and descends into madness.',
            'joy': 0.05, 'surprise': 0.6, 'anger': 0.3, 'fear': 0.95, 'sadness': 0.4
        },
        {
            'isbn13': '9780062315007',
            'title': 'To Kill a Mockingbird',
            'authors': 'Harper Lee',
            'simple_categories': 'Fiction',
            'num_pages': 250,
            'description': 'A classic novel about racial injustice and moral growth in the American South during the 1930s.',
            'joy': 0.3, 'surprise': 0.4, 'anger': 0.6, 'fear': 0.3, 'sadness': 0.5
        },
        {
            'isbn13': '9780062059925',
            'title': 'Outliers',
            'authors': 'Malcolm Gladwell',
            'simple_categories': 'Non-Fiction',
            'num_pages': 180,
            'description': 'An exploration of what makes high-achievers different and the hidden advantages that contribute to success.',
            'joy': 0.6, 'surprise': 0.8, 'anger': 0.1, 'fear': 0.1, 'sadness': 0.2
        },
        {
            'isbn13': '9780385737951',
            'title': 'Charlie and the Chocolate Factory',
            'authors': 'Roald Dahl',
            'simple_categories': "Children's Fiction",
            'num_pages': 120,
            'description': 'A delightful tale about a poor boy who wins a golden ticket to tour the most magnificent chocolate factory in the world.',
            'joy': 0.95, 'surprise': 0.9, 'anger': 0.05, 'fear': 0.1, 'sadness': 0.1
        },
        {
            'isbn13': '9780439136365',
            'title': 'National Geographic Kids Almanac 2023',
            'authors': 'National Geographic Kids',
            'simple_categories': "Children's Non-Fiction",
            'num_pages': 80,
            'description': 'An educational almanac packed with facts, photos, and fun activities about animals, science, geography, and world cultures.',
            'joy': 0.7, 'surprise': 0.5, 'anger': 0.05, 'fear': 0.05, 'sadness': 0.1
        },
        {
            'isbn13': '9780544173767',
            'title': 'A Short History of Nearly Everything',
            'authors': 'Bill Bryson',
            'simple_categories': 'Non-Fiction',
            'num_pages': 350,
            'description': 'A fascinating journey through science and history, explaining complex scientific concepts in an accessible and entertaining way.',
            'joy': 0.5, 'surprise': 0.6, 'anger': 0.1, 'fear': 0.1, 'sadness': 0.2
        },
        {
            'isbn13': '9780307743657',
            'title': 'It',
            'authors': 'Stephen King',
            'simple_categories': 'Fiction',
            'num_pages': 1138,
            'description': 'A terrifying horror novel about a group of children who face an ancient evil entity in the town of Derry, Maine.',
            'joy': 0.02, 'surprise': 0.8, 'anger': 0.4, 'fear': 0.98, 'sadness': 0.6
        },
        {
            'isbn13': '9780439064873',
            'title': 'Harry Potter and the Chamber of Secrets',
            'authors': 'J.K. Rowling',
            'simple_categories': "Children's Fiction",
            'num_pages': 341,
            'description': 'Harry returns to Hogwarts for his second year and faces the mystery of the Chamber of Secrets and its deadly monster.',
            'joy': 0.7, 'surprise': 0.8, 'anger': 0.2, 'fear': 0.4, 'sadness': 0.2
        }
    ]
    
    return pd.DataFrame(data)
