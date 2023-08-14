

declare -A CONF=(
'aaai' 'db/conf/aaai/aaai~~~~.bht'
'clikm' 'db/conf/cikm/cikm~~~~.bht'
'cvpr' 'db/conf/cvpr/cvpr~~~~.bht'
'cvprw' 'db/conf/cvpr/cvpr~~~~w.bht'
'iclr' 'db/conf/iclr/iclr~~~~.bht'
'ijcai' 'db/conf/ijcai/ijcai~~~~.bht'
'sigir' 'db/conf/sigir/sigir~~~~.bht'
'wsdm' 'db/conf/wsdm/wsdm~~~~.bht'
'www' 'db/conf/www/www~~~~.bht'
)

declare -A START=(
'aaai' 2010
'cvpr' 2000
'cvprw' 2000
'iclr' 2013
'cikm' 2000
'sigir' 2000
)


declare -a keys=('iclr')

END_YEAR=$(date -d 'now' +%Y)
for key in $keys; do
    for (( j=${START[$key]}; j<=END_YEAR; j++)); do
        python -u ./export_records_from_dblp.py --bht "${CONF[$key]/~~~~/$j}"
    done
done
