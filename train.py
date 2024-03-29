import json
import os
import pprint

import mlflow.sklearn
import mlflow.sklearn
import numpy as np
from keras.layers.core import Dense
from keras.models import Sequential
from keras.optimizers import SGD
from sklearn.externals import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2


def vectorize_video_input(video):
    input_vector = [0] * num_tags
    for tag in video["tags"]:
        tag_index = tag_to_index.get(tag, None)
        if tag_index is not None:
            input_vector[tag_index] = 1
    return input_vector


def vectorize_video_target(video):
    target_vector = [0] * num_categories
    category_index = category_id_to_index.get(video["target_category_id"], None)
    if category_index is not None:
        target_vector[category_index] = 1
    return target_vector


if __name__ == "__main__":
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/videos.json")
    ) as json_file:
        videos = json.load(json_file)

    pprint.pprint(videos[0])

    tags = set()

    for video in videos:
        for tag in video["tags"]:
            tags.add(tag)

    num_tags = len(tags)
    tag_to_index = {tag: index for index, tag in enumerate(tags)}

    print("The first video input in vector form looks like this:")
    print(vectorize_video_input(videos[0]))

    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/categories.json")
    ) as json_file:
        categories = json.load(json_file)

    num_categories = len(categories)

    print("We have {} categories:".format(num_categories))
    pprint.pprint(categories)

    category_id_to_index = {
        category["id"]: index for index, category in enumerate(categories)
    }
    print("Category id to index in target vector:")
    print(category_id_to_index)
    print("The first video target category in one-hot-vector form looks like this:")
    print(vectorize_video_target(videos[0]))

    input_vectors = [vectorize_video_input(video) for video in videos]
    target_vectors = [vectorize_video_target(video) for video in videos]

    epochs = 50
    input_vectors = np.array(input_vectors)
    target_vectors = np.array(target_vectors)

    training_fraction = 0.8  # use e.g. 80 % of data for training, 20 % for validation
    split_index = int(len(input_vectors) * training_fraction)
    training_input_vectors = input_vectors[0:split_index]
    training_target_vectors = target_vectors[0:split_index]
    validation_input_vectors = input_vectors[split_index:]
    validation_target_vectors = target_vectors[split_index:]

    num_hidden_nodes = 10
    model = Sequential()
    model.add(Dense(num_hidden_nodes, input_dim=num_tags, activation="relu"))
    model.add(Dense(num_categories, activation="softmax"))

    model.compile(
        loss="categorical_crossentropy",
        optimizer=SGD(momentum=0.0),
        metrics=["accuracy"],
    )

    model.fit(training_input_vectors, training_target_vectors, epochs=epochs)

    evaluation_scores = model.evaluate(
        validation_input_vectors, validation_target_vectors
    )

    # model.predict expects a list of examples (a 2D numpy array)
    # We will put only one example in our list of examples
    output_vectors = model.predict(np.array([input_vectors[-1]]))
    output_vector = output_vectors[0]

    joblib.dump(model, "model/model.pkl")
    # model.save('model/model.pkl', model)
    print("Output vector: {}".format(str(output_vector)))
    print("Target vector: {}".format(str(target_vectors[-1])))

    # ======================================== mlflow expermiment ===========================

    experiment_name = "aia-deep-learning-sess-001"
    expr_id = mlflow.set_experiment(experiment_name)
    with mlflow.start_run(experiment_id=expr_id, run_name="deeplearning-11"):
        (rmse, mae, r2) = eval_metrics(target_vectors[-1], output_vector)
        for i, metric_name in enumerate(model.metrics_names):
            mlflow.log_metric(metric_name, evaluation_scores[i])
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)
        mlflow.log_metric("mae", mae)

        # log parameters
        mlflow.log_param("epoch", epochs)
        mlflow.log_param("data", "videos.json")
        # log model
        mlflow.sklearn.log_model(model, "model")

        # log input artifacts
        data = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "data"
        )
        mlflow.log_artifacts(data)
