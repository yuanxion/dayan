#!/usr/bin/env bash
set -euo pipefail

export no_proxy=127.0.0.1,intel.com,.intel.com,10.0.0.0/8,192.168.0.0/16,localhost,.local,127.0.0.0/8,134.134.0.0/16

# ILSVRC2012_img_val
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
dataset_dir="${1:-$script_dir/tasks/001-colorization-v2/artifacts/datasets}"
mkdir -p "$dataset_dir"
archive="$dataset_dir/ILSVRC2012_img_val.tar"
url='https://image-net.org/data/ILSVRC/2012/ILSVRC2012_img_val.tar'

if command -v wget >/dev/null 2>&1; then
	wget --continue --timeout=10 --tries=2 --directory-prefix="$dataset_dir" "$url"
elif command -v curl >/dev/null 2>&1; then
	curl --fail --location --connect-timeout 10 --retry 1 --retry-connrefused \
		--continue-at - --output "$archive" "$url"
else
	echo 'Install GNU wget or curl to download the dataset.' >&2
	exit 127
fi

# # roberta-base-mrpc
# folder=ov-share-02-data-nn_icv_cv_externalN-omz-validation-datasets/GLUE_MRPC_roberta/model_attributes/roberta-base-mrpc
# mkdir -p $folder
# wget -P $folder -c https://ov-share-02.iotg.sclab.intel.com/nn_icv_cv_externalN/omz-validation-datasets/model_attributes/roberta-base-mrpc/merges.txt
# wget -P $folder -c https://ov-share-02.iotg.sclab.intel.com/nn_icv_cv_externalN/omz-validation-datasets/model_attributes/roberta-base-mrpc/special_tokens_map.json
# wget -P $folder -c https://ov-share-02.iotg.sclab.intel.com/nn_icv_cv_externalN/omz-validation-datasets/model_attributes/roberta-base-mrpc/tokenizer.json
# wget -P $folder -c https://ov-share-02.iotg.sclab.intel.com/nn_icv_cv_externalN/omz-validation-datasets/model_attributes/roberta-base-mrpc/tokenizer_config.json
# wget -P $folder -c https://ov-share-02.iotg.sclab.intel.com/nn_icv_cv_externalN/omz-validation-datasets/model_attributes/roberta-base-mrpc/vocab.json
