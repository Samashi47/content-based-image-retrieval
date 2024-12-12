# content-based-image-retrieval

Welcome to our web application designed to implement a robust Content-Based Image Retrieval (CBIR) system that enables efficient image search and management through visual features and relevance feedback mechanisms. Users can upload, download, delete, and categorize images into predefined classes, as well as generate new images by applying transformations like cropping and scaling. The system computes and displays visual descriptors for images, including color histograms, dominant colors, Gabor texture filters, Hu moments, and additional custom descriptors. It supports both basic search to retrieve visually similar images and an advanced Bayesian relevance feedback mechanism to iteratively refine results, providing an intuitive and dynamic way to explore the RSSCN7 dataset, which consists of 2,800 images categorized into seven scene types such as Residential, Forest, and Industry.

## Installation

To start off, clone this branch of the repo into your local:

```shell
git clone https://github.com/Samashi47/content-based-image-retrieval.git
```

```shell
cd content-based-image-retrieval
```

### Backend

After cloning the project, if you are using Python 3.12.z with shared libraries enabled, you can checkout to the `edge` branch, using the latest pymc version:

```shell
git checkout edge
```

If not, you can stay on the `main` branch.

Then, create a virtual environment:

```shell
cd apps/api
```

**Windows**

```shell
py -3 -m venv .venv
```

**MacOS/Linus**

```shell
python3 -m venv .venv
```

Then, activate the env:

**Windows**

```shell
.venv\Scripts\activate
```

**MacOS/Linus**

```shell
. .venv/bin/activate
```

You can run the following command to install the dependencies:

```shell
pip3 install -r requirements.txt
```

After installing the dependencies, you should specify the mongodb connection string in the `.env` file:

```shell
touch .env
```

```env
MONGO_URL=<url>
```

Then, you can run the following command to start the backend:

```shell
python server.py
```

### Frontend

Open another terminal:

```shell
cd apps/app
```

Then, run the following command to install the dependencies:

```shell
pnpm install
```

then, run the following command to start the frontend, if you have angular cli installed globally:

```shell
ng serve
```

if not, you can run the following command:

```shell
pnpm run ng serve
```

Then, open your browser and navigate to `http://localhost:4200/` to see the app running.
