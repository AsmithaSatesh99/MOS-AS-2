from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from irsystem import ImageSearchEngine
from config import Config
import os
from datetime import datetime
import nltk
nltk.download('stopwords',silent=True)

app = Flask(__name__)
app.config['APP_NAME'] = "Visual Voyager"
app.config.from_object(Config)

# Initialize search engine
search_engine = ImageSearchEngine()

@app.context_processor
def inject_now():
    """Make 'now' available in all templates"""
    return {'now': datetime.now()}

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = app.config['PER_PAGE']
    
    all_images = search_engine.get_all_images()
    print(all_images[0])
    total_images = len(all_images)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_images = all_images[start:end]
    
    return render_template('index.html',
                        images=paginated_images,
                         page=page,
                         per_page=per_page,
                         total_images=total_images,
                         start=start,
                         end=end)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        method = request.form.get('method', 'vsm')
        return redirect(url_for('search_results', query=query, method=method))
    
    return redirect(url_for('index'))

@app.route('/search/results')
def search_results():
    query = request.args.get('query', '')
    method = request.args.get('method', 'vsm')
    
    if not query:
        return redirect(url_for('index'))
    
    if method == 'vsm':
        results = search_engine.search_vsm(query)
    elif method == 'bm25':
        results = search_engine.search_bm25(query)
    # else:
    #     results = search_engine.search_semantic(query)
    
    return render_template('results.html',
                         query=query,
                         method=method,
                         results=results)

@app.route('/image/<filename>')
def image_detail(filename):
    image_data = next((img for img in search_engine.image_metadata 
                      if img['filename'] == filename), None)
    
    if not image_data:
        return redirect(url_for('index'))
    
    return render_template('image.html', image=image_data)

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['IMAGE_FOLDER'], filename)

if __name__ == '__main__':
    # Create thumbnails directory if it doesn't exist
    if not os.path.exists(app.config['THUMBNAIL_FOLDER']):
        os.makedirs(app.config['THUMBNAIL_FOLDER'])
    
    app.run(debug=True)