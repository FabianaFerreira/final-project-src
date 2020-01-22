from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.applications import VGG16
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, CSVLogger, LambdaCallback
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from datetime import datetime

import numpy as np
import pandas as pd

BATCH_SIZE = 64


def createModel(img_rows=224, img_cols=224, channel=3, num_classes=None):
    # Load the VGG model
    base_model = VGG16(weights='imagenet', include_top=False, input_shape=(img_rows, img_cols, channel))

    # loop over all layers in the base model and freeze them so they will
    # *not* be updated during the first training process
    for layer in base_model.layers:
        layer.trainable = False

    model = Sequential()

    model.add(base_model)
    model.add(Flatten())
    model.add(Dense(512, kernel_initializer='he_uniform'))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes, activation='softmax'))

    # Show a summary of the model. Check the number of trainable parameters
    model.summary()

    # Learning rate is changed to 0.001
    sgd = SGD(lr=1e-3, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(optimizer=sgd, loss='categorical_crossentropy', metrics=['accuracy'])

    return model


# Loading data
X_train = np.load('./datasets/CNN/X_train_no_edge_frames_subset.npy')
X_test = np.load('./datasets/CNN/X_test_no_edge_frames_subset.npy')
y_train = np.load('./datasets/CNN/y_train_no_edge_frames_subset.npy')
y_test = np.load('./datasets/CNN/y_test_no_edge_frames_subset.npy')

# Creating model
model = createModel(num_classes=7)

y_train = np.argmax(y_train, axis=1).astype(str)
y_test = np.argmax(y_test, axis=1).astype(str)

# df_train = pd.concat([pd.DataFrame({'X': X_train}), pd.DataFrame(y_train)], axis=1)
# df_test = pd.concat([pd.DataFrame({'X': X_test}), pd.DataFrame(y_test)], axis=1)
df_train = pd.DataFrame({'X': X_train, 'y': y_train})
df_test = pd.DataFrame({'X': X_test, 'y': y_test})
# class_columns = [str(x) for x in (set(df_train.columns) - {'X'})]

train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    shear_range=0.3,
    zoom_range=0.3,
    horizontal_flip=False,
    vertical_flip=False,
    validation_split=0.2
)

train_gen = train_datagen.flow_from_dataframe(
    dataframe=df_train,
    x_col='X',
    y_col='y',
    target_size=(224, 224),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    color_mode='rgb',
    subset='training')  # set as training data

validation_gen = train_datagen.flow_from_dataframe(
    dataframe=df_train,
    x_col='X',
    y_col='y',
    target_size=(224, 224),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    color_mode='rgb',
    subset='validation')

# train_gen = DataGenerator(X_train, y_train, 64)
# test_gen = DataGenerator(X_test, y_test, 64)

# Defining callbacks
# TODO: Check if folder exist and create them if not
epochs_to_wait_for_improvement = 10
logging_path = './logs'
models_path = './models'
model_name = 'fine_tune_VGG16_no_edge_frames_' + datetime.today().strftime('%Y-%m-%d-%H:%M:%S')

print_weights = LambdaCallback(on_epoch_end=lambda batch, logs: print(model.layers[0].get_weights()))
early_stopping = EarlyStopping(monitor='val_loss', patience=epochs_to_wait_for_improvement)
checkpoint = ModelCheckpoint(f'{models_path}/{model_name}.h5', monitor='val_loss', save_best_only=True, mode='min')
csv_logger = CSVLogger(f'{logging_path}/{model_name}.log')

callbacks = [early_stopping, checkpoint, csv_logger, print_weights]

print('Training model... You should get a coffee...')
# Fit the model
print(model.summary())
# print(model_name)
# exit(1)
model.fit_generator(
    generator=train_gen,
    steps_per_epoch=train_gen.samples // BATCH_SIZE,
    epochs=1000,
    verbose=1,
    validation_data=validation_gen,
    validation_steps=validation_gen.samples // BATCH_SIZE,
    callbacks=callbacks,
    # class_weight=[12.39411284, 5.43687231, 11.48333333, 4.59194184, 9.109375, 5.06617647, 8.10588235]
    # class_weight=[2, 1, 2, 1, 1.5, 1, 1.5]
    # class_weight=[1.76699708, 0.7763886, 1.63858549, 0.65533498, 1.30395869,
    #               0.72539257, 1.15690616]
)

# train_generator,
#     steps_per_epoch = train_generator.samples // batch_size,
#     validation_data = validation_generator,
#     validation_steps = validation_generator.samples // batch_size,